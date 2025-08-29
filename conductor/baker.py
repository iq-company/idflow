#!/usr/bin/env python3
import argparse, hashlib, json, os, re, subprocess, sys
from pathlib import Path

try:
	import yaml  # pip install pyyaml
except Exception as e:
	print("Please install pyyaml (pip install pyyaml)", file=sys.stderr)
	raise

DEFAULT_SETTINGS = {
	"registry": "ghcr.io",
	"owner": "",
	"platforms": ["linux/amd64"],
	"push": True,
	"check": "auto",  # auto|local|remote
	"builder": "",
	"namespace_prefix": "",
	"hash": { "tag_length": 8 },
}

# ---------- subprocess helpers ----------
def run(cmd, check=True, capture=False):
	kwargs = {}
	if capture:
		kwargs["stdout"] = subprocess.PIPE
		kwargs["stderr"] = subprocess.STDOUT
		kwargs["text"] = True
	p = subprocess.run(cmd, **kwargs)
	if check and p.returncode != 0:
		msg = f"Command failed ({p.returncode}): {' '.join(cmd)}"
		if capture:
			msg += f"\n----\n{p.stdout}\n----"
		raise RuntimeError(msg)
	return p

# --- helpers for overrides / coercion ---
import json, re

TRUE_SET  = {"true","1","yes","on"}
FALSE_SET = {"false","0","no","off"}

def parse_value(val: str):
	s = str(val).strip()
	low = s.lower()
	if low in TRUE_SET:  return True
	if low in FALSE_SET: return False
	# JSON?
	if (s.startswith("[") and s.endswith("]")) or (s.startswith("{") and s.endswith("}")) or (s.startswith('"') and s.endswith('"')):
		try: return json.loads(s)
		except Exception: pass
	# Zahl?
	if re.fullmatch(r"-?\d+", s):  return int(s)
	if re.fullmatch(r"-?\d+\.\d+", s): return float(s)
	# Kommagetrennte Liste?
	if "," in s: return [x.strip() for x in s.split(",")]
	return s

def set_deep(d: dict, dotted_key: str, raw_value: str):
	keys = dotted_key.split(".")
	cur = d
	for k in keys[:-1]:
		if k not in cur or not isinstance(cur[k], dict):
			cur[k] = {}
		cur = cur[k]
	cur[keys[-1]] = parse_value(raw_value)

def coerce_bools(settings: dict):
	# Top-level: push -> bool, check bleibt string
	if isinstance(settings.get("push"), str):
		settings["push"] = parse_value(settings["push"])
	# targets.*.latest -> bool
	for t in settings.get("targets", {}).values():
		if isinstance(t.get("latest"), str):
			t["latest"] = parse_value(t["latest"])
	return settings

# ---------- hashing ----------
def sha256_file(p: Path) -> str:
	h = hashlib.sha256()
	with p.open("rb") as f:
		for chunk in iter(lambda: f.read(65536), b""):
			h.update(chunk)
	return h.hexdigest()

def sha256_bytes(b: bytes) -> str:
	return hashlib.sha256(b).hexdigest()

def short_hash(h: str, n: int) -> str:
	return (h or "")[:max(1, int(n) or 8)]

# ---------- interpolation (top-level strings) ----------
INTERP_RE = re.compile(r"\$\{([^}]+)\}")

def env_func(name, default=""):
	return os.getenv(name, default)

def read_file_func(path):
	data = Path(path).read_text(encoding="utf-8")
	return data.strip()

def checksum_files_func(*paths):
	h = hashlib.sha256()
	for p in paths:
		with open(p, "rb") as f:
			for chunk in iter(lambda: f.read(65536), b""):
				h.update(chunk)
	return h.hexdigest()

def git_short_sha_func():
	try:
		out = run(["git","rev-parse","--short","HEAD"], capture=True, check=True).stdout.strip()
		return out
	except Exception:
		return "nogit"

def concat_func(*args):
	return "".join(str(a) for a in args)

def normalize_tag(s: str) -> str:
	# Docker tag charset: [A-Za-z0-9_.-]
	s = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(s))
	return s.strip("-") or "untagged"

def interpolate_scalar(s: str) -> str:
	# Interpolate ${...} in arbitrary strings in settings (registry, owner, etc.)
	def repl(m):
		expr = m.group(1).strip()
		# Allow only env(), readFile(), checksum(), gitShortSha(), concat()
		# (No currentChecksum here - that's target-scoped)
		safe_env = {
			"env": env_func,
			"readFile": read_file_func,
			"checksum": checksum_files_func,
			"gitShortSha": git_short_sha_func,
			"concat": concat_func,
		}
		try:
			val = eval(expr, {"__builtins__": {}}, safe_env)
		except Exception as e:
			raise ValueError(f"Interpolation error in '{s}': {e}") from e
		return str(val)
	return INTERP_RE.sub(repl, s)

def deep_interpolate(node):
	# Walk dict/list and interpolate strings with ${...}
	if isinstance(node, dict):
		return {k: deep_interpolate(v) for k, v in node.items()}
	if isinstance(node, list):
		return [deep_interpolate(x) for x in node]
	if isinstance(node, str) and "${" in node:
		return interpolate_scalar(node)
	return node

# ---------- settings load ----------
def load_settings(path: str|None) -> dict:
	s = dict(DEFAULT_SETTINGS)
	p = path or "build-settings.yml"
	with open(p, "r", encoding="utf-8") as f:
		raw = yaml.safe_load(f) or {}
		if not isinstance(raw, dict):
			raise ValueError("settings file must be a mapping at top level.")
	# first-pass interpolate (for registry/owner/etc.)
	raw = deep_interpolate(raw)
	# Deep-merge hash settings
	s.update({k:v for k,v in raw.items() if k != "hash"})
	if "hash" in raw:
		s["hash"] = { **DEFAULT_SETTINGS["hash"], **(raw.get("hash") or {}) }

	# env overrides for registry/owner remain possible
	s["registry"] = os.getenv("REGISTRY", s.get("registry"))
	owner = os.getenv("OWNER", s.get("owner") or "")
	if not owner:
		owner = os.getenv("GITHUB_REPOSITORY_OWNER","")
	s["owner"] = owner

	if "targets" not in s or not isinstance(s["targets"], dict) or not s["targets"]:
		raise ValueError("'targets' must be a non-empty mapping in settings.")
	if "bundles" in s and not isinstance(s["bundles"], dict):
		raise ValueError("'bundles' must be a mapping if present.")
	s.setdefault("bundles", {})

	# normalize targets
	for name, t in s["targets"].items():
		if "dockerfile" not in t:
			raise ValueError(f"Target '{name}' missing 'dockerfile'.")
		t.setdefault("context", ".")
		t.setdefault("build_args", {})
		t.setdefault("hash_files", [t["dockerfile"]])
		t.setdefault("deps", [])
		t.setdefault("hash_mode", "self")
		t.setdefault("image", name)
		t.setdefault("latest", False)
		# tag may be present; currentChecksum() etc. are evaluated later (target-scoped)

	return s

# ---------- graph utils ----------
def expand_targets(settings, names):
	# keine Bundles mehr – nur direkte Targets + transitive Deps
	targets = settings["targets"]
	if not names:							   # nichts angegeben -> alle
		return list(targets.keys())
	selected = set()
	def add_with_deps(n):
		if n in selected: return
		if n not in targets:
			raise KeyError(f"Unknown target: {n}")
		for d in targets[n].get("deps", []):
			add_with_deps(d)
		selected.add(n)
	for n in names:
		add_with_deps(n)
	return list(selected)						# spätere topo_sort sorgt für Reihenfolge

def topo_sort(settings: dict, selected: list[str]) -> list[str]:
	targets = settings["targets"]
	visited, order = set(), []

	def dfs(n: str, stack: set):
		if n in visited: return
		if n in stack: raise ValueError(f"Cycle detected at '{n}'")
		stack.add(n)
		for d in targets[n].get("deps", []):
			if d in selected: dfs(d, stack)
		stack.remove(n)
		visited.add(n)
		order.append(n)

	for n in selected: dfs(n, set())
	return order

# ---------- checksums ----------
def compute_self_hash(settings: dict, tname: str) -> str:
	t = settings["targets"][tname]
	h = hashlib.sha256()

	# Dateien hashen
	for f in t.get("hash_files", [t["dockerfile"]]):
		p = Path(f)
		if not p.exists():
			raise FileNotFoundError(f"Hash file not found: {f} (target {tname})")
		with p.open("rb") as fp:
			for chunk in iter(lambda: fp.read(65536), b""):
				h.update(chunk)

	# Build-Args deterministisch einfließen lassen (nach Interpolation!)
	# Sortierte key=value-Linien, damit stabil.
	ba = t.get("build_args", {}) or {}
	for k in sorted(ba.keys()):
		v = "" if ba[k] is None else str(ba[k])
		h.update(f"\nARG {k}={v}".encode("utf-8"))

	return h.hexdigest()

def compute_full_hash(settings: dict, tname: str, memo: dict[str,str]) -> str:
	if tname in memo: return memo[tname]
	t = settings["targets"][tname]
	self_hash = compute_self_hash(settings, tname)
	if t.get("hash_mode","self") == "self+deps":
		dep_hashes = [compute_full_hash(settings, d, memo) for d in sorted(t.get("deps", []))]
		payload = ("".join(dep_hashes) + self_hash).encode("utf-8")
		memo[tname] = sha256_bytes(payload)
	else:
		memo[tname] = self_hash
	return memo[tname]

def compute_all_hashes(settings: dict, selected: list[str]) -> dict[str,str]:
	memo = {}
	for n in selected:
		compute_full_hash(settings, n, memo)
	return {n: memo[n] for n in selected}

# ---------- tag expression (target-scoped) ----------
def eval_tag_expr(expr: str, settings: dict, tname: str, hashes: dict[str,str]) -> str:
	safe_env = {
		"env": env_func,
		"readFile": read_file_func,
		"checksum": checksum_files_func,
		"gitShortSha": git_short_sha_func,
		"concat": concat_func,
		# target-scoped:
		"currentChecksum": lambda: hashes[tname],
		"currentChecksum8": lambda: short_hash(hashes[tname], n),
		"depChecksum": lambda name: hashes.get(name, ""),
		"short": lambda s: short_hash(str(s), n),
	}
	try:
		val = eval(expr, {"__builtins__": {}}, safe_env)
	except Exception as e:
		raise ValueError(f"Tag expression error in target '{tname}': {e}") from e
	return normalize_tag(val)

def compute_tags(settings: dict, selected: list[str]) -> dict[str,str]:
	hashes = compute_all_hashes(settings, selected)
	n = settings.get("hash",{}).get("tag_length", 8)
	tags = {}
	for tname in selected:
		t = settings["targets"][tname]
		expr = t.get("tag")
		if isinstance(expr, str):
			# (gleich wie bisher) – Ausdrücke/Strings unverändert auswerten
			if expr.startswith("${") and expr.endswith("}"):
				inner = expr[2:-1].strip()
				tags[tname] = eval_tag_expr(inner, settings, tname, hashes)
			elif "${" in expr:
				def repl(m): return eval_tag_expr(m.group(1), settings, tname, hashes)
				tags[tname] = normalize_tag(re.sub(r"\$\{([^}]+)\}", repl, expr))
			else:
				tags[tname] = normalize_tag(expr)
		else:
			# Kein tag angegeben → kurzer Hash
			tags[tname] = short_hash(hashes[tname], n)
	return tags

# ---------- image refs / existence ----------
def image_ref(settings: dict, tname: str, tag: str) -> str:
	img = settings["targets"][tname]["image"]
	prefix = settings.get("namespace_prefix", "")
	if prefix:
		img = f"{prefix}-{img}"

	parts = []
	reg = (settings.get("registry") or "").strip()
	own = (settings.get("owner") or "").strip()

	# nur nicht-leere Teile anhängen
	if reg:
		parts.append(reg)
	if own:
		parts.append(own)
	parts.append(img)

	repo = "/".join(parts)				# z.B. "builder-ui" oder "ghcr.io/owner/builder-ui"
	repo = re.sub(r"/{2,}", "/", repo).lstrip("/")

	return f"{repo}:{tag}"

def image_exists_local(ref: str) -> bool:
	p = run(["docker","image","inspect", ref], check=False, capture=True)
	return p.returncode == 0

def image_exists_remote(ref: str) -> bool:
	p = run(["docker","buildx","imagetools","inspect", ref], check=False, capture=True)
	return p.returncode == 0

def want_remote_check(settings: dict, explicit: str|None) -> bool:
	mode = explicit or settings.get("check","auto")
	if mode == "local": return False
	if mode == "remote": return True
	return bool(settings.get("push", True))  # auto

# ---------- HCL generation ----------
def gen_hcl(settings: dict, tags: dict[str, str], targets_subset=None) -> str:
	targets = settings["targets"]; bundles = settings["bundles"]
	subset = targets_subset or list(targets.keys())
	out = []

	for tname in subset:
		t = targets[tname]
		tag = tags[tname]

		# --- Auto-Args aus deps via image_ref(...) ---
		auto_args = {}
		for dep in t.get("deps", []):
			key = f"IMAGE_{dep.replace('-', '_').upper()}"
			dep_tag = tags.get(dep)

			if dep_tag is None:
				# Fallback: eigenen Tag für dep schnell berechnen (zur Not nur self-Hash)
				raise KeyError(f"Missing tag for dependency '{dep}' when generating HCL for '{tname}'")

			auto_args[key] = image_ref(settings, dep, dep_tag)

		# User-Args haben Vorrang:
		user_args = t.get("build_args", {}) or {}
		all_args = {**auto_args, **user_args}

		out += [
			"",
			f'target "{tname}" {{',
			f'	context = "{t["context"]}"',
			f'	dockerfile = "{t["dockerfile"]}"',
		]

		if all_args:
			out.append("  args = {")
			for k in sorted(all_args):
				out.append(f'	 {k} = "{all_args[k]}",')
			out.append("  }")

		out.append("  tags = [")
		out.append(f'	 "{image_ref(settings, tname, tag)}",')
		if t.get("latest", False):
			out.append(f'	 "{image_ref(settings, tname, "latest")}",')
		out.append("  ]")
		out.append("}")

	# FIXME: correct?
	# optional: default-Gruppe für bakes ohne Zielnamen
	if subset:
		lst = ",".join(f'"{x}"' for x in subset)
		out.append('\n# default group')
		out.append(f'group "default" {{ targets = [{lst}] }}')

	return "\n".join(out) + "\n"

# ---------- plan / build ----------
def plan(settings: dict, args, selected_override: list[str] | None = None):
	if selected_override is not None:
		selected = selected_override
	else:
		selected = select_targets(settings, args.targets)

	tags = compute_tags(settings, selected)
	remote = want_remote_check(settings, args.check)

	to_build, decisions = [], {}
	for n in selected:
		ref = image_ref(settings, n, tags[n])
		exists = image_exists_remote(ref) if remote else image_exists_local(ref)
		reason = "exists-remote" if (remote and exists) else ("exists-local" if (not remote and exists) else "missing")
		force = n in (args.force or [])
		skip  = n in (args.skip  or [])
		build = (force or not exists) and not skip
		decisions[n] = {"tag": tags[n], "ref": ref, "exists": exists, "reason": reason, "build": build, "force": force, "skip": skip}
		if build:
			to_build.append(n)
		if args.end and n in args.end:
			break

	return selected, tags, to_build, decisions

def do_build(settings: dict, args, to_build: list[str], tags: dict[str, str]):
	"""
	Build die 'to_build'-Targets sequenziell.
	- HCL wird für die gesamte Auswahl (Closure über --targets) erzeugt,
	  damit Auto-Args (IMAGE_*) alle Dep-Tags kennen.
	- Bei push=false laden wir ins lokale Docker-Image-Store (--load).
	"""
	from pathlib import Path

	# 1) Auswahl bestimmen (Closure über --targets); falls nichts angegeben -> alle
	selected = select_targets(settings, args.targets)

	if not to_build:
		print("Nothing to build.")
		return

	# 2) HCL für die gesamte Auswahl erzeugen (damit Dep-IMAGE_* korrekt sind)
	hcl = gen_hcl(settings, tags, targets_subset=selected)
	tmp = Path(".bake.tmp.hcl")
	tmp.write_text(hcl, encoding="utf-8")

	try:
		# 3) Gemeinsame Kommando-Basis
		cmd = ["docker", "buildx", "bake", "-f", str(tmp)]
		if settings.get("builder"):
			cmd += ["--builder", settings["builder"]]
		if settings.get("platforms"):
			cmd += ["--set", f"*.platform={','.join(settings['platforms'])}"]

		push_flag = args.push if args.push is not None else settings.get("push", True)
		base_cmd = cmd + (["--push"] if push_flag else ["--load"])

		# 4) Sequenziell bauen (stabil bzgl. FROM-Dependencies)
		for t in to_build:
			print("RUN:", " ".join(base_cmd + [t]))
			run(base_cmd + [t])

	finally:
		if not getattr(args, "keep_hcl", False):
			tmp.unlink(missing_ok=True)
		else:
			print(f"Kept temp HCL at {tmp}")

def select_targets(settings: dict, names: list[str] | None) -> list[str]:
	tdefs = settings["targets"]
	if not names:
		# nichts angegeben -> alle Targets
		selected = list(tdefs.keys())
		return topo_sort(settings, selected)

	acc = set()
	def add(n: str):
		if n in acc:
			return
		if n not in tdefs:
			raise KeyError(f"Unknown target: {n}")
		for d in tdefs[n].get("deps", []):
			add(d)
		acc.add(n)

	for n in names:
		add(n)
	return topo_sort(settings, list(acc))

# ---------- CLI ----------
def main():
	ap = argparse.ArgumentParser(prog="baker", description="Docker build target planner (YAML-defined).")
	ap.add_argument("--settings", default="build-settings.yml", help="Path to settings.yml (default: build-settings.yml)")
	ap.add_argument("--set", dest="overrides", action="append", default=[], help="Override config property, e.g. --set push=false or --set targets.srv.latest=false")
	sub = ap.add_subparsers(dest="cmd", required=True)

	def tgt_opts(p):
		p.add_argument("--targets", nargs="*", help="targets or bundles (default: all)")
		p.add_argument("--force", nargs="*", default=[], help="force specific targets")
		p.add_argument("--skip", nargs="*", default=[], help="skip specific targets")
		p.add_argument("--end", nargs="*", default=[], help="stop planning at these targets")
		p.add_argument("--check", choices=["auto","local","remote"], default=None)
		p.add_argument("--push", dest="push", action=argparse.BooleanOptionalAction, default=None)

	p_plan = sub.add_parser("plan", help="Show plan and what would build")
	tgt_opts(p_plan)
	p_plan.add_argument("--json", action="store_true", help="machine-readable output")
	p_plan.add_argument("--print-env", action="store_true", help="print TAG_<TARGET> vars")

	p_hcl = sub.add_parser("gen-hcl", help="Generate docker-bake.hcl from YAML")
	tgt_opts(p_hcl)
	p_hcl.add_argument("-o","--output", nargs="?", const="-", default="docker-bake.hcl")

	p_build = sub.add_parser("build", help="Build (and optionally push) via buildx bake")
	tgt_opts(p_build)

	args = ap.parse_args()
	settings = load_settings(args.settings)

	# apply overrides
	for ov in args.overrides:
		if "=" not in ov:
			raise SystemExit(f"--set expects key=value, got: {ov}")
		k, v = ov.split("=", 1)
		set_deep(settings, k.strip(), v)
	settings = coerce_bools(settings)

	selected, tags, to_build, decisions = plan(settings, args)

	if args.cmd == "plan":
		if args.print_env:
			for n in selected:
				envname = f"TAG_{n.replace('-','_').upper()}"
				print(f"{envname}={decisions[n]['tag']}")
		if args.json:
			print(json.dumps({"selected": selected, "decisions": decisions}, indent=2))
		else:
			for n in selected:
				d = decisions[n]
				mark = "BUILD" if d["build"] else "skip"
				print(f"{n:<22} {d['tag'][:12]}  {mark:5} ({d['reason']})  {d['ref']}")
			print("\nWill build:" if to_build else "\nNothing to build.", ", ".join(to_build))
		return

	if args.cmd == "gen-hcl":
		selected = select_targets(settings, args.targets)
		# plan nur, um die Tags (inkl. Deps) zu bekommen – decisions brauchst du hier nicht
		_sel, tags, _to_build, _dec = plan(settings, args, selected_override=selected)
		hcl = gen_hcl(settings, tags, targets_subset=selected)	# <— Closure in die Datei

		if args.output == "-":
			print(hcl, end="")
		else:
			Path(args.output).write_text(hcl, encoding="utf-8")
			print(f"Wrote {args.output}")
		return

	if args.cmd == "build":
		do_build(settings, args, to_build, {n: decisions[n]["tag"] for n in selected})
		return

if __name__ == "__main__":
	main()

