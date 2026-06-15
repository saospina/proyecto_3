"""Build the OpenAPI 3 spec for the JSON API from Pydantic schemas."""
from __future__ import annotations

from typing import Any, Dict

from pydantic.json_schema import GenerateJsonSchema, models_json_schema

from app.schemas import (
    TaskGenerationSchema,
    TaskListGenerationSchema,
    TaskSchema,
    UserStoryGenerationSchema,
    UserStorySchema,
)


class _ComponentRefGenerator(GenerateJsonSchema):
    """Emit `$ref` pointers into `#/components/schemas/...` instead of `#/$defs/...`."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.definitions_path = "components/schemas"

    def generate(self, schema, mode="validation"):  # type: ignore[override]
        out = super().generate(schema, mode=mode)
        out.pop("$defs", None)
        return out


USER_STORY_EXAMPLE: Dict[str, Any] = {
    "id": 1,
    "project": "Acme Dashboard",
    "role": "marketing manager",
    "goal": "export my campaign dashboard as a PDF",
    "reason": "I can share weekly results with non-technical stakeholders",
    "description": (
        "As a marketing manager, I want to export the campaign dashboard as a PDF "
        "so that I can share weekly results with non-technical stakeholders. "
        "The export should preserve charts, branding, and current filters."
    ),
    "priority": "high",
    "story_points": 5,
    "effort_hours": 12.5,
    "acceptance_criteria": (
        "- A 'Download PDF' button is visible on the dashboard.\n"
        "- The exported PDF preserves applied filters.\n"
        "- File is delivered within 10 seconds for dashboards of up to 50 widgets."
    ),
    "created_at": "2026-06-15T10:30:00+00:00",
}

TASK_EXAMPLE: Dict[str, Any] = {
    "id": 7,
    "title": "Implement PDF rendering service",
    "description": (
        "Add a backend service that takes a dashboard ID and applied filters and returns "
        "a rendered PDF. Use headless Chromium and reuse the existing chart components."
    ),
    "priority": "high",
    "effort_hours": 6.0,
    "status": "pending",
    "assigned_to": "backend",
    "user_story_id": 1,
    "created_at": "2026-06-15T10:35:00+00:00",
}

CREATE_USER_STORY_REQUEST_EXAMPLE: Dict[str, Any] = {
    "prompt": (
        "The marketing team wants registered users to be able to export the campaign "
        "dashboard as a PDF, preserving filters and branding, so they can share weekly "
        "results with non-technical stakeholders."
    )
}


def _components_schemas() -> Dict[str, Any]:
    """Return Pydantic-derived JSON Schemas keyed by short component name."""
    _, top = models_json_schema(
        [
            (UserStorySchema, "validation"),
            (TaskSchema, "validation"),
            (UserStoryGenerationSchema, "validation"),
            (TaskGenerationSchema, "validation"),
            (TaskListGenerationSchema, "validation"),
        ],
        ref_template="#/components/schemas/{model}",
        schema_generator=_ComponentRefGenerator,
    )
    return top.get("$defs", {})


def build_openapi_spec() -> Dict[str, Any]:
    schemas = _components_schemas()

    schemas["Error"] = {
        "type": "object",
        "required": ["error"],
        "properties": {
            "error": {"type": "string", "example": "user_story_not_found"},
            "detail": {"type": "string", "example": "UserStory 42 not found"},
            "id": {"type": "integer", "example": 42},
        },
    }
    schemas["CreateUserStoryRequest"] = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Free-form description of the feature, stakeholder, or problem.",
                "minLength": 1,
            }
        },
        "example": CREATE_USER_STORY_REQUEST_EXAMPLE,
    }

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "AI Backlog API",
            "version": "1.0.0",
            "description": (
                "JSON API for generating and inspecting AI-produced user stories and tasks. "
                "All AI calls go through OpenAI structured outputs validated by Pydantic."
            ),
        },
        "servers": [{"url": "/", "description": "This server"}],
        "tags": [
            {"name": "user-stories", "description": "Manage AI-generated user stories."},
            {"name": "tasks", "description": "Manage AI-generated implementation tasks."},
        ],
        "paths": {
            "/api/v1/user-stories": {
                "get": {
                    "tags": ["user-stories"],
                    "summary": "List all user stories",
                    "description": "Return every user story stored in the database, newest first.",
                    "responses": {
                        "200": {
                            "description": "List of user stories.",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/UserStorySchema"},
                                    },
                                    "examples": {
                                        "two-stories": {
                                            "summary": "Two stored stories",
                                            "value": [USER_STORY_EXAMPLE],
                                        }
                                    },
                                }
                            },
                        }
                    },
                },
                "post": {
                    "tags": ["user-stories"],
                    "summary": "Generate a user story from a prompt",
                    "description": (
                        "Send a natural-language prompt; the AI returns a complete user story "
                        "which is validated against `UserStoryGenerationSchema` and stored."
                    ),
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/CreateUserStoryRequest"
                                },
                                "examples": {
                                    "pdf-export": {
                                        "summary": "Export dashboard as PDF",
                                        "value": CREATE_USER_STORY_REQUEST_EXAMPLE,
                                    }
                                },
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "User story successfully generated and stored.",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/UserStorySchema"},
                                    "example": USER_STORY_EXAMPLE,
                                }
                            },
                        },
                        "400": {
                            "description": "Empty or missing prompt.",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"},
                                    "example": {"error": "prompt_required"},
                                }
                            },
                        },
                        "502": {
                            "description": "AI generation failed.",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"},
                                    "example": {
                                        "error": "generation_failed",
                                        "detail": "OpenAI returned no parsed user story",
                                    },
                                }
                            },
                        },
                    },
                },
            },
            "/api/v1/user-stories/{story_id}": {
                "parameters": [
                    {
                        "name": "story_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                        "example": 1,
                    }
                ],
                "get": {
                    "tags": ["user-stories"],
                    "summary": "Get a single user story",
                    "responses": {
                        "200": {
                            "description": "The requested user story.",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/UserStorySchema"},
                                    "example": USER_STORY_EXAMPLE,
                                }
                            },
                        },
                        "404": {
                            "description": "User story not found.",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"},
                                    "example": {"error": "user_story_not_found", "id": 42},
                                }
                            },
                        },
                    },
                },
            },
            "/api/v1/user-stories/{story_id}/tasks": {
                "parameters": [
                    {
                        "name": "story_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                        "example": 1,
                    }
                ],
                "get": {
                    "tags": ["tasks"],
                    "summary": "List tasks for a user story",
                    "responses": {
                        "200": {
                            "description": "Tasks for the given user story.",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/TaskSchema"},
                                    },
                                    "example": [TASK_EXAMPLE],
                                }
                            },
                        },
                        "404": {
                            "description": "User story not found.",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"},
                                    "example": {"error": "user_story_not_found", "id": 42},
                                }
                            },
                        },
                    },
                },
            },
            "/api/v1/user-stories/{story_id}/generate-tasks": {
                "parameters": [
                    {
                        "name": "story_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                        "example": 1,
                    }
                ],
                "post": {
                    "tags": ["tasks"],
                    "summary": "Generate tasks for a user story",
                    "description": (
                        "Ask the AI to break the user story into 3–8 implementation tasks. "
                        "The tasks are validated against `TaskListGenerationSchema` and inserted "
                        "in a single commit."
                    ),
                    "responses": {
                        "201": {
                            "description": "Tasks successfully generated and stored.",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/TaskSchema"},
                                    },
                                    "example": [TASK_EXAMPLE],
                                }
                            },
                        },
                        "404": {
                            "description": "User story not found.",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"},
                                    "example": {"error": "user_story_not_found", "id": 42},
                                }
                            },
                        },
                        "502": {
                            "description": "AI generation failed.",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"},
                                    "example": {
                                        "error": "generation_failed",
                                        "detail": "OpenAI returned no parsed tasks",
                                    },
                                }
                            },
                        },
                    },
                },
            },
        },
        "components": {"schemas": schemas},
    }
