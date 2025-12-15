"""
Web UI for text-glosser using FastAPI and NiceGUI.

This module provides the web interface for the text-glosser application.
"""

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI
from nicegui import ui

from ..core.exporters import export_all_formats
from ..core.ingestion import fetch_url, read_file
from ..core.models import TextSource
from ..core.processor import TextProcessor
from ..core.registry import get_registry
from ..core.session import get_session_manager
from ..utils.security import sanitize_filename, sanitize_session_id, sanitize_url

# Language code to name mapping (ISO 639-1 codes)
LANGUAGE_NAMES = {
    "ar": "Arabic",
    "en": "English",
    "fr": "French",
    "de": "German",
    "el": "Greek",
    "he": "Hebrew",
    "la": "Latin",
    "sa": "Sanskrit",
    "zh": "Chinese",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "hi": "Hindi",
    "bn": "Bengali",
    "pa": "Punjabi",
    "te": "Telugu",
    "mr": "Marathi",
    "ta": "Tamil",
    "ur": "Urdu",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "or": "Odia",
}

def get_language_display_name(lang_code: str) -> str:
    """
    Get human-readable language name with code.

    Parameters
    ----------
    lang_code : str
        ISO 639 language code

    Returns
    -------
    str
        Display name like "Chinese (zh)" or just "(zh)" if name unknown
    """
    name = LANGUAGE_NAMES.get(lang_code)
    if name:
        return f"{name} ({lang_code})"
    return f"({lang_code})"

# Initialize FastAPI app
app = FastAPI(title="Text Glosser", version="0.1.0")

# Initialize components
registry = get_registry()
session_manager = get_session_manager()
processor = TextProcessor(registry)

# Create data directories
DATA_DIR = Path("./data")
UPLOADS_DIR = DATA_DIR / "uploads"
RESULTS_DIR = DATA_DIR / "results"
USER_RESOURCES_DIR = DATA_DIR / "user_resources"

for dir_path in [DATA_DIR, UPLOADS_DIR, RESULTS_DIR, USER_RESOURCES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/dictionaries")
async def get_dictionaries(language: str | None = None):
    """Get list of available dictionaries."""
    if language:
        resources = registry.get_resources_by_language(language)
    else:
        resources = registry.get_all_resources()

    return {
        "dictionaries": [
            {
                "id": res.id,
                "name": res.name,
                "format": res.format.value,
                "type": res.resource_type.value,
                "primary_language": res.primary_language,
                "secondary_languages": res.secondary_languages,
                "is_user_provided": res.is_user_provided,
                "accessible": registry.verify_resource_accessible(res.id),
            }
            for res in resources
        ]
    }


@app.get("/api/languages")
async def get_languages():
    """Get list of languages that have resources."""
    languages = registry.get_all_languages()

    # Prioritized languages list
    priority_languages = ["ar", "en", "fr", "de", "el", "he", "la", "sa", "zh"]

    # Separate into priority and other
    priority = [lang for lang in priority_languages if lang in languages]
    other = sorted([lang for lang in languages if lang not in priority_languages])

    return {
        "priority": priority,
        "other": other,
        "all": priority + other,
    }


# NiceGUI UI
def create_main_page():
    """Create the main landing page."""

    # State management
    state = {
        "selected_resources": [],
        "uploaded_files": [],
        "retention_days": 180,
        "enable_retention": True,
        "session_id": None,
        "text_sources": [],
    }

    with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
        # Header
        ui.markdown("# Text Glosser")
        ui.markdown("Analyze text using linguistic dictionaries and resources")

        ui.separator()

        # Session settings
        with ui.card().classes("w-full"):
            ui.markdown("## Session Settings")

            with ui.row().classes("w-full items-center gap-4"):
                retention_enabled = ui.checkbox(
                    "Delete my data after inactive days:", value=True
                )
                retention_input = ui.number(
                    "Days",
                    value=180,
                    min=0,
                    max=365,
                    step=1,
                ).classes("w-32")

                def on_retention_toggle(e):
                    if not e.value:
                        # Disabled
                        retention_input.value = 0
                        retention_input.disable()
                    else:
                        # Enabled
                        if retention_input.value == 0:
                            retention_input.value = 180
                        retention_input.enable()

                def on_retention_change(e):
                    if e.value == 0:
                        retention_enabled.value = False
                        retention_input.disable()

                retention_enabled.on_value_change(on_retention_toggle)
                retention_input.on_value_change(on_retention_change)

        ui.separator()

        # Dictionary selection
        with ui.card().classes("w-full"):
            ui.markdown("## Select Dictionaries and Resources")

            # Group by language
            grouped = registry.get_resources_grouped_by_language()

            selected_resources_list = []
            language_checkboxes = {}  # Track language-level checkboxes

            for lang_code in sorted(grouped.keys()):
                resources = grouped[lang_code]
                lang_display = get_language_display_name(lang_code)

                # Create a container for the language group
                with ui.row().classes("w-full items-center gap-2"):
                    # Master checkbox for the language group
                    lang_checkbox = ui.checkbox(
                        f"Select all {lang_display}", value=False
                    )
                    language_checkboxes[lang_code] = {
                        "master": lang_checkbox,
                        "items": [],
                    }

                with ui.expansion(
                    f"Language: {lang_display}", icon="translate"
                ).classes("w-full") as expansion:
                    resource_checkboxes_for_lang = []

                    for res in resources:
                        accessible = registry.verify_resource_accessible(res.id)
                        prefix = "[User]" if res.is_user_provided else "[Built-in]"

                        checkbox = ui.checkbox(
                            f"{prefix} {res.name} ({res.format.value})", value=False
                        )

                        if not accessible:
                            checkbox.disable()
                            ui.label("⚠️ Not accessible").classes("text-red-500 text-sm")

                        selected_resources_list.append((checkbox, res.id))
                        resource_checkboxes_for_lang.append(checkbox)

                    language_checkboxes[lang_code]["items"] = (
                        resource_checkboxes_for_lang
                    )

                # Connect master checkbox to expand and select all items
                def create_lang_handler(lang_code, expansion_widget, checkboxes):
                    def on_lang_check(e):
                        # The event value indicates whether checkbox is checked
                        checked = e.value

                        # Expand the group when checked
                        if checked:
                            expansion_widget.open()

                        # Set all child checkboxes to the same value
                        for cb in checkboxes:
                            # Check if checkbox is enabled
                            if not cb._props.get("disable", False):
                                cb.value = checked

                    return on_lang_check

                lang_checkbox.on_value_change(
                    create_lang_handler(
                        lang_code,
                        expansion,
                        resource_checkboxes_for_lang,
                    )
                )

            state["resource_checkboxes"] = selected_resources_list
            state["language_checkboxes"] = language_checkboxes

            # Upload dictionaries button
            ui.button(
                "Upload Dictionaries/Resources",
                on_click=lambda: ui.notify("Dictionary upload coming soon!"),
            ).classes("mt-4")

        ui.separator()

        # Text source input
        with ui.card().classes("w-full"):
            ui.markdown("## Text Sources")

            # File upload
            ui.markdown("### Upload Files")

            def handle_upload(e):
                """Handle file upload event."""
                try:
                    # e.name contains the filename
                    # e.content contains file content as BytesIO object
                    file_name = e.name
                    file_content = e.content

                    # Save uploaded file
                    file_path = UPLOADS_DIR / sanitize_filename(file_name)
                    with open(file_path, "wb") as f:
                        f.write(file_content.read())

                    # Read content as text
                    content = read_file(str(file_path))

                    # Create TextSource
                    text_source = TextSource(
                        id=str(uuid.uuid4()),
                        name=file_name,
                        content=content,
                        source_type="file",
                        original_path=str(file_path),
                    )

                    state["text_sources"].append(text_source)
                    ui.notify(f"File added: {file_name}", type="positive")

                except Exception as e:
                    ui.notify(f"Error loading file: {e}", type="negative")
                    import traceback
                    traceback.print_exc()

            ui.upload(
                label="Select text files (auto-uploads on selection)",
                multiple=True,
                on_upload=handle_upload,
            ).classes("w-full")

            # URL input
            ui.markdown("### Or Enter URLs")
            url_input = ui.textarea(
                "URLs (one per line)",
                placeholder="https://example.com/text1\nhttps://example.com/text2",
            ).classes("w-full")

            ui.button(
                "Add URLs", on_click=lambda: handle_url_input(url_input.value, state)
            )

        # Process button
        ui.separator()

        ui.button(
            "Process Text", on_click=lambda: process_text(state), color="primary"
        ).classes("text-lg px-8 py-4")



def handle_url_input(urls_text, state):
    """Handle URL input."""
    if not urls_text:
        ui.notify("Please enter at least one URL", type="warning")
        return

    urls = [url.strip() for url in urls_text.split("\n") if url.strip()]

    for url in urls:
        try:
            # Validate and fetch
            clean_url = sanitize_url(url)
            if not clean_url:
                ui.notify(f"Invalid URL: {url}", type="negative")
                continue

            content = fetch_url(clean_url)

            # Create TextSource
            text_source = TextSource(
                id=str(uuid.uuid4()),
                name=url,
                content=content,
                source_type="url",
                original_path=url,
            )

            state["text_sources"].append(text_source)
            ui.notify(f"Added URL: {url}", type="positive")

        except Exception as e:
            ui.notify(f"Error fetching {url}: {e}", type="negative")


def process_text(state):
    """Process text with selected resources."""
    # Get selected resources
    selected_resources = [
        res_id
        for checkbox, res_id in state.get("resource_checkboxes", [])
        if checkbox.value
    ]

    if not selected_resources:
        ui.notify("Please select at least one dictionary/resource", type="warning")
        return

    if not state.get("text_sources"):
        ui.notify("Please upload files or enter URLs", type="warning")
        return

    try:
        # Create session
        session = session_manager.create_session(
            text_sources=state["text_sources"],
            selected_resources=selected_resources,
            retention_days=state.get("retention_days"),
        )

        # Process each text source
        results = []
        for text_source in state["text_sources"]:
            analysis = processor.analyze_text(text_source, selected_resources)
            results.append(analysis)

        # Export results
        output_dir = RESULTS_DIR / session.session_id
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, analysis in enumerate(results):
            base_filename = Path(state["text_sources"][i].name).stem
            export_all_formats(analysis, str(output_dir), base_filename)

        ui.notify(
            f"Processing complete! Session ID: {session.session_id}", type="positive"
        )

        # Navigate to results page
        ui.navigate.to(f"/results/{session.session_id}")

    except Exception as e:
        ui.notify(f"Error processing text: {e}", type="negative")
        import traceback

        traceback.print_exc()


@ui.page("/")
def index():
    """Main page route."""
    create_main_page()


@ui.page("/results/{session_id}")
def results_page(session_id: str):
    """Results page."""
    session_id = sanitize_session_id(session_id)
    if not session_id:
        ui.label("Invalid session ID")
        return

    session = session_manager.get_session(session_id)
    if not session:
        ui.label("Session not found")
        return

    with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
        ui.markdown(f"# Results - Session {session_id}")

        ui.button("Back to Home", on_click=lambda: ui.navigate.to("/")).classes("mb-4")

        # Show results
        results_dir = RESULTS_DIR / session_id
        if results_dir.exists():
            files = list(results_dir.glob("*"))

            ui.markdown(f"## Files ({len(files)})")

            for file_path in files:
                with ui.row().classes("items-center gap-2"):
                    ui.label(file_path.name)
                    ui.button(
                        "Download", on_click=lambda fp=file_path: ui.download(str(fp))
                    )

        # Delete session button
        ui.separator()
        ui.button(
            "Delete Session Data",
            on_click=lambda: delete_session(session_id),
            color="red",
        )


def delete_session(session_id: str):
    """Delete a session."""
    try:
        session_manager.delete_session(session_id)

        # Delete results
        results_dir = RESULTS_DIR / session_id
        if results_dir.exists():
            shutil.rmtree(results_dir)

        ui.notify("Session deleted", type="positive")
        ui.navigate.to("/")

    except Exception as e:
        ui.notify(f"Error deleting session: {e}", type="negative")


# Initialize NiceGUI with FastAPI
ui.run_with(
    app,
    storage_secret="change-this-to-a-random-secret-key-in-production",
    title="Text Glosser",
)
