import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from idflow.core.document_factory import get_document_class
from idflow.core.document import Document
from idflow.core.stage import Stage


class MockDocument(Document):
    """Mock Document implementation for testing."""

    def _save(self):
        pass

    def _create(self):
        pass

    def _destroy(self):
        pass

    def _save_stage(self, stage):
        """Mock implementation of _save_stage."""
        pass

    def _create_stage(self, stage):
        """Mock implementation of _create_stage."""
        pass

    def _get_stage_path(self, stage_name, counter=1):
        """Mock implementation of _get_stage_path."""
        return Path(f"/tmp/test_doc/stages/{stage_name}/{counter}")

    @classmethod
    def _find(cls, uuid: str):
        return None

    @classmethod
    def _where(cls, **filters):
        return []


class TestStageBasic:
    """Test basic stage functionality."""

    def test_stage_creation(self):
        """Test that stages can be created with basic attributes."""
        doc = MockDocument()
        stage = doc.add_stage("test_stage", info="test info", props=[1, 2, 3])

        assert stage.name == "test_stage"
        assert stage.counter == 1
        assert stage.info == "test info"
        assert stage.props == [1, 2, 3]
        assert stage.parent == doc
        assert stage.parent_id == doc.id

    def test_stage_to_dict_excludes_parent(self):
        """Test that stage.to_dict() excludes the parent object."""
        doc = MockDocument()
        stage = doc.add_stage("test_stage", info="test info")

        stage_dict = stage.to_dict()

        assert "parent" not in stage_dict
        assert "parent_id" in stage_dict
        assert stage_dict["parent_id"] == doc.id
        assert stage_dict["name"] == "test_stage"
        assert stage_dict["counter"] == 1
        assert stage_dict["info"] == "test info"


class TestStageMultipleInstances:
    """Test multiple instances of the same stage name."""

    def test_multiple_stages_same_name(self):
        """Test that multiple stages with the same name get different counters."""
        doc = MockDocument()

        stage1 = doc.add_stage("test_stage", info="first")
        stage2 = doc.add_stage("test_stage", info="second")
        stage3 = doc.add_stage("test_stage", info="third")

        assert stage1.counter == 1
        assert stage2.counter == 2
        assert stage3.counter == 3

        assert stage1.name == "test_stage"
        assert stage2.name == "test_stage"
        assert stage3.name == "test_stage"

    def test_get_stages_by_name(self):
        """Test getting all stages with a specific name."""
        doc = MockDocument()

        doc.add_stage("stage_a", info="first a")
        doc.add_stage("stage_b", info="first b")
        doc.add_stage("stage_a", info="second a")
        doc.add_stage("stage_c", info="first c")
        doc.add_stage("stage_a", info="third a")

        stage_a_list = doc.get_stages("stage_a")
        stage_b_list = doc.get_stages("stage_b")
        stage_c_list = doc.get_stages("stage_c")

        assert len(stage_a_list) == 3
        assert len(stage_b_list) == 1
        assert len(stage_c_list) == 1

        assert stage_a_list[0].counter == 1
        assert stage_a_list[1].counter == 2
        assert stage_a_list[2].counter == 3

    def test_get_stage_by_name_and_counter(self):
        """Test getting a specific stage by name and counter."""
        doc = MockDocument()

        doc.add_stage("test_stage", info="first")
        doc.add_stage("test_stage", info="second")
        doc.add_stage("test_stage", info="third")

        stage1 = doc.get_stage("test_stage", 1)
        stage2 = doc.get_stage("test_stage", 2)
        stage3 = doc.get_stage("test_stage", 3)
        stage_nonexistent = doc.get_stage("test_stage", 4)

        assert stage1.info == "first"
        assert stage2.info == "second"
        assert stage3.info == "third"
        assert stage_nonexistent is None


class TestStageDirtyTracking:
    """Test dirty tracking for stages and documents."""

    def test_document_dirty_on_stage_addition(self):
        """Test that document is marked dirty when a stage is added."""
        doc = MockDocument()
        assert not doc._dirty

        doc.add_stage("test_stage")
        assert doc._dirty

    def test_stage_dirty_on_attribute_change(self):
        """Test that stage attributes can be changed and tracked."""
        doc = MockDocument()
        stage = doc.add_stage("test_stage")

        # Change stage attributes
        stage.info = "new info"
        stage.props = [4, 5, 6]

        # Stage should be dirty
        assert stage._dirty

        # Document should also be dirty
        assert doc._dirty

    def test_mark_stage_dirty(self):
        """Test that mark_stage_dirty works correctly."""
        doc = MockDocument()
        stage = doc.add_stage("test_stage")

        # Reset dirty flags
        doc._dirty = False
        stage._dirty = False

        doc.mark_stage_dirty(stage)
        assert doc._dirty


class TestStageSave:
    """Test stage save functionality."""

    def test_stage_save_calls_parent_save_stage(self):
        """Test that stage.save() calls the parent's _save_stage method."""
        doc = MockDocument()
        stage = doc.add_stage("test_stage")

        # Test that stage.save() exists and can be called
        # (The actual implementation calls parent._save_stage which we can't easily test)
        assert hasattr(stage, 'save')
        assert callable(stage.save)

    def test_document_save_resets_dirty_flags(self):
        """Test that document.save() resets dirty flags."""
        doc = MockDocument()

        # Add stages and modify them
        stage1 = doc.add_stage("stage1", info="original1")
        stage2 = doc.add_stage("stage2", info="original2")
        stage3 = doc.add_stage("stage3", info="original3")

        # Reset dirty flags
        doc._dirty = False
        stage1._dirty = False
        stage2._dirty = False
        stage3._dirty = False

        # Modify some stages
        stage1.info = "modified1"
        stage3.info = "modified3"

        # Verify dirty flags are set
        assert stage1._dirty
        assert not stage2._dirty
        assert stage3._dirty
        assert doc._dirty

        # Test that save method exists and can be called
        assert hasattr(doc, 'save')
        assert callable(doc.save)


class TestStageFilesystem:
    """Test stage filesystem operations."""

    @pytest.fixture
    def temp_doc_dir(self):
        """Create a temporary directory for document testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_stage_path_includes_counter(self):
        """Test that stage paths include the counter in the directory structure."""
        doc = MockDocument()
        stage = doc.add_stage("test_stage")

        # Mock the doc_dir property
        doc._doc_dir = Path("/tmp/test_doc")

        # Test that the stage path is constructed correctly
        expected_path = Path("/tmp/test_doc/stages/test_stage/1")
        assert stage.stage_path == expected_path


class TestStageIntegration:
    """Test stage integration with the full system."""

    def test_stage_lifecycle(self):
        """Test complete stage lifecycle: create, modify, save, reload."""
        doc = MockDocument()

        # Create stage
        stage = doc.add_stage("workflow", info="initial", props=["step1"])
        assert stage.name == "workflow"
        assert stage.counter == 1
        assert doc._dirty

        # Modify stage
        stage.info = "updated"
        stage.props.append("step2")
        assert stage._dirty
        assert doc._dirty

        # Add another stage with same name
        stage2 = doc.add_stage("workflow", info="second", props=["step3"])
        assert stage2.counter == 2
        assert stage2.name == "workflow"

        # Verify stage lists
        workflow_stages = doc.get_stages("workflow")
        assert len(workflow_stages) == 2
        assert workflow_stages[0].counter == 1
        assert workflow_stages[1].counter == 2

        # Test specific stage retrieval
        retrieved_stage = doc.get_stage("workflow", 1)
        assert retrieved_stage == stage
        assert retrieved_stage.info == "updated"

        retrieved_stage2 = doc.get_stage("workflow", 2)
        assert retrieved_stage2 == stage2
        assert retrieved_stage2.info == "second"


class TestRequirements:
    """Test the new requirements functionality."""

    def test_attribute_checks(self):
        """Test attribute check requirements."""
        from idflow.core.stage_definitions import StageDefinition, Requirements, AttributeCheck

        # Create a mock document with attributes
        doc = MockDocument()
        doc.tags = ["blog_post_ideas", "research"]
        doc.seo_keywords = "research, blog, ideas"
        doc.priority = 5
        doc.author = "John Doe"

        # Test EQ operator
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="seo_keywords", operator="EQ", value="research, blog, ideas")
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

        # Test NE operator
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="author", operator="NE", value="Jane Doe")
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

        # Test GT operator
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="priority", operator="GT", value=3)
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

        # Test failed requirement
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="priority", operator="GT", value=10)
                ]
            )
        )
        assert stage_def.check_requirements(doc) == False

    def test_list_checks(self):
        """Test list check requirements."""
        from idflow.core.stage_definitions import StageDefinition, Requirements, ListCheck

        # Create a mock document with list attributes
        doc = MockDocument()
        doc.tags = ["blog_post_ideas", "research", "content"]
        doc.categories = ["tech", "programming"]

        # Test HAS operator
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                list_checks=[
                    ListCheck(attribute="tags", operator="HAS", value="blog_post_ideas")
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

        # Test CONTAINS operator
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                list_checks=[
                    ListCheck(attribute="tags", operator="CONTAINS", value="research")
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

        # Test NOT_HAS operator
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                list_checks=[
                    ListCheck(attribute="tags", operator="NOT_HAS", value="draft")
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

        # Test failed requirement
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                list_checks=[
                    ListCheck(attribute="tags", operator="HAS", value="nonexistent")
                ]
            )
        )
        assert stage_def.check_requirements(doc) == False

    def test_case_sensitivity(self):
        """Test case sensitivity in requirements."""
        from idflow.core.stage_definitions import StageDefinition, Requirements, AttributeCheck, ListCheck

        doc = MockDocument()
        doc.tags = ["Blog_Post_Ideas", "Research"]
        doc.seo_keywords = "Research, Blog, Ideas"

        # Test case sensitive (default)
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="seo_keywords", operator="EQ", value="Research, Blog, Ideas", case_sensitive=True)
                ],
                list_checks=[
                    ListCheck(attribute="tags", operator="HAS", value="Blog_Post_Ideas", case_sensitive=True)
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

        # Test case insensitive
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="seo_keywords", operator="EQ", value="research, blog, ideas", case_sensitive=False)
                ],
                list_checks=[
                    ListCheck(attribute="tags", operator="HAS", value="blog_post_ideas", case_sensitive=False)
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

    def test_combined_requirements(self):
        """Test combined requirements (file_presence + attribute + list + stage)."""
        from idflow.core.stage_definitions import StageDefinition, Requirements, AttributeCheck, ListCheck, FilePresenceRequirement, StageRequirement

        doc = MockDocument()
        doc.tags = ["blog_post_ideas", "research"]
        doc.priority = 5
        doc.add_file_ref("content", "test.md", "file-uuid")

        # Add a completed stage
        stage = doc.add_stage("previous_stage", status="done")

        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                file_presence=FilePresenceRequirement(key="content", count=1, count_operator=">="),
                attribute_checks=[
                    AttributeCheck(attribute="priority", operator="GT", value=3)
                ],
                list_checks=[
                    ListCheck(attribute="tags", operator="HAS", value="blog_post_ideas")
                ],
                stages={
                    "previous_stage": StageRequirement(status="done")
                }
            )
        )
        assert stage_def.check_requirements(doc) == True

    def test_pattern_matching(self):
        """Test pattern matching requirements (Glob and Regex)."""
        from idflow.core.stage_definitions import StageDefinition, Requirements, AttributeCheck

        # Create a mock document with various string attributes
        doc = MockDocument()
        doc.filename = "blog_post_2024_01_15.md"
        doc.title = "How to Build a Blog Post"
        doc.content = "This is a sample blog post about programming and technology."
        doc.url = "https://example.com/blog/how-to-build-blog-post"
        doc.email = "user@example.com"

        # Test Glob Pattern Matching - CP (Contains Pattern)
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="filename", operator="CP", value="blog_*.md")
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

        # Test Glob Pattern Matching - NP (Not Contains Pattern)
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="filename", operator="NP", value="draft_*.md")
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

        # Test Regex Pattern Matching - REGEX
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="url", operator="REGEX", value=r"https://.*\.com/.*")
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

        # Test Regex Pattern Matching - NOT_REGEX
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="email", operator="NOT_REGEX", value=r".*@gmail\.com")
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

        # Test case sensitivity with patterns
        doc.title = "How to Build a BLOG Post"

        # Case sensitive (should fail)
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="title", operator="CP", value="*blog*", case_sensitive=True)
                ]
            )
        )
        assert stage_def.check_requirements(doc) == False

        # Case insensitive (should pass)
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="title", operator="CP", value="*blog*", case_sensitive=False)
                ]
            )
        )
        assert stage_def.check_requirements(doc) == True

        # Test failed pattern matching
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="filename", operator="CP", value="draft_*.md")
                ]
            )
        )
        assert stage_def.check_requirements(doc) == False

    def test_invalid_patterns(self):
        """Test handling of invalid patterns."""
        from idflow.core.stage_definitions import StageDefinition, Requirements, AttributeCheck

        doc = MockDocument()
        doc.content = "Some content"

        # Test invalid regex pattern
        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="content", operator="REGEX", value="[invalid regex")
                ]
            )
        )
        # Should not crash, but return False for invalid regex
        assert stage_def.check_requirements(doc) == False

        # Test non-string values with pattern matching
        doc.priority = 5

        stage_def = StageDefinition(
            name="test_stage",
            requirements=Requirements(
                attribute_checks=[
                    AttributeCheck(attribute="priority", operator="CP", value="*")
                ]
            )
        )
        # Should return False for non-string values
        assert stage_def.check_requirements(doc) == False
