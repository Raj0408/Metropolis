"""
AI Tools Marketplace for Metropolis
Provides a comprehensive collection of pre-built AI tools and integrations
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from .models import AITool, User
from .ai_schemas import AIToolCreate, AIToolUpdate

logger = logging.getLogger(__name__)

class AIToolsMarketplace:
    """
    AI Tools Marketplace with pre-built integrations for popular AI services
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.predefined_tools = self._get_predefined_tools()
    
    def _get_predefined_tools(self) -> List[Dict[str, Any]]:
        """Get predefined AI tools for the marketplace"""
        return [
            # OpenAI Tools
            {
                "name": "OpenAI GPT-4",
                "description": "Advanced language model for text generation, analysis, and conversation",
                "category": "Language Models",
                "provider": "OpenAI",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "enum": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                            "default": "gpt-4"
                        },
                        "temperature": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 2,
                            "default": 0.7
                        },
                        "max_tokens": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 4096,
                            "default": 1000
                        }
                    },
                    "required": ["model"]
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The input prompt for the model"
                        },
                        "system_message": {
                            "type": "string",
                            "description": "Optional system message to set context"
                        }
                    },
                    "required": ["prompt"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "The generated response"
                        },
                        "usage": {
                            "type": "object",
                            "properties": {
                                "prompt_tokens": {"type": "integer"},
                                "completion_tokens": {"type": "integer"},
                                "total_tokens": {"type": "integer"}
                            }
                        }
                    }
                }
            },
            {
                "name": "OpenAI DALL-E",
                "description": "AI image generation from text descriptions",
                "category": "Image Generation",
                "provider": "OpenAI",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "enum": ["dall-e-2", "dall-e-3"],
                            "default": "dall-e-3"
                        },
                        "size": {
                            "type": "string",
                            "enum": ["1024x1024", "1024x1792", "1792x1024"],
                            "default": "1024x1024"
                        },
                        "quality": {
                            "type": "string",
                            "enum": ["standard", "hd"],
                            "default": "standard"
                        }
                    },
                    "required": ["model"]
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Text description of the image to generate"
                        }
                    },
                    "required": ["prompt"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "image_url": {
                            "type": "string",
                            "description": "URL of the generated image"
                        },
                        "revised_prompt": {
                            "type": "string",
                            "description": "The revised prompt used for generation"
                        }
                    }
                }
            },
            
            # Hugging Face Tools
            {
                "name": "Hugging Face Text Classification",
                "description": "Classify text into predefined categories",
                "category": "Text Analysis",
                "provider": "Hugging Face",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "default": "distilbert-base-uncased-finetuned-sst-2-english"
                        },
                        "max_length": {
                            "type": "integer",
                            "default": 512
                        }
                    }
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to classify"
                        }
                    },
                    "required": ["text"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "predictions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {"type": "string"},
                                    "score": {"type": "number"}
                                }
                            }
                        }
                    }
                }
            },
            {
                "name": "Hugging Face Sentiment Analysis",
                "description": "Analyze sentiment of text (positive, negative, neutral)",
                "category": "Text Analysis",
                "provider": "Hugging Face",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "default": "cardiffnlp/twitter-roberta-base-sentiment-latest"
                        }
                    }
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to analyze sentiment for"
                        }
                    },
                    "required": ["text"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "sentiment": {
                            "type": "string",
                            "enum": ["positive", "negative", "neutral"]
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        }
                    }
                }
            },
            
            # Google AI Tools
            {
                "name": "Google Gemini Pro",
                "description": "Google's advanced multimodal AI model",
                "category": "Language Models",
                "provider": "Google",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "enum": ["gemini-pro", "gemini-pro-vision"],
                            "default": "gemini-pro"
                        },
                        "temperature": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "default": 0.7
                        }
                    }
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Input prompt for the model"
                        },
                        "image": {
                            "type": "string",
                            "description": "Base64 encoded image (for vision models)"
                        }
                    },
                    "required": ["prompt"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "Generated response"
                        }
                    }
                }
            },
            
            # Data Processing Tools
            {
                "name": "Text Preprocessor",
                "description": "Clean and preprocess text data",
                "category": "Data Processing",
                "provider": "Metropolis",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "remove_punctuation": {
                            "type": "boolean",
                            "default": True
                        },
                        "lowercase": {
                            "type": "boolean",
                            "default": True
                        },
                        "remove_stopwords": {
                            "type": "boolean",
                            "default": False
                        },
                        "stem_words": {
                            "type": "boolean",
                            "default": False
                        }
                    }
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to preprocess"
                        }
                    },
                    "required": ["text"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "processed_text": {
                            "type": "string",
                            "description": "Preprocessed text"
                        },
                        "original_length": {
                            "type": "integer",
                            "description": "Original text length"
                        },
                        "processed_length": {
                            "type": "integer",
                            "description": "Processed text length"
                        }
                    }
                }
            },
            {
                "name": "Data Validator",
                "description": "Validate and clean structured data",
                "category": "Data Processing",
                "provider": "Metropolis",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "schema": {
                            "type": "object",
                            "description": "JSON schema for validation"
                        },
                        "strict_mode": {
                            "type": "boolean",
                            "default": False
                        }
                    },
                    "required": ["schema"]
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "object",
                            "description": "Data to validate"
                        }
                    },
                    "required": ["data"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "is_valid": {
                            "type": "boolean",
                            "description": "Whether data is valid"
                        },
                        "errors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Validation errors if any"
                        },
                        "cleaned_data": {
                            "type": "object",
                            "description": "Cleaned data"
                        }
                    }
                }
            },
            
            # Computer Vision Tools
            {
                "name": "Image Classifier",
                "description": "Classify images into predefined categories",
                "category": "Computer Vision",
                "provider": "TensorFlow",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "default": "mobilenet_v2"
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "default": 0.5
                        }
                    }
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "image": {
                            "type": "string",
                            "description": "Base64 encoded image or image URL"
                        }
                    },
                    "required": ["image"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "predictions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "class": {"type": "string"},
                                    "confidence": {"type": "number"}
                                }
                            }
                        }
                    }
                }
            },
            {
                "name": "Object Detector",
                "description": "Detect and locate objects in images",
                "category": "Computer Vision",
                "provider": "YOLO",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "default": "yolov8n"
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "default": 0.5
                        }
                    }
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "image": {
                            "type": "string",
                            "description": "Base64 encoded image or image URL"
                        }
                    },
                    "required": ["image"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "detections": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "class": {"type": "string"},
                                    "confidence": {"type": "number"},
                                    "bbox": {
                                        "type": "object",
                                        "properties": {
                                            "x": {"type": "number"},
                                            "y": {"type": "number"},
                                            "width": {"type": "number"},
                                            "height": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            
            # Audio Processing Tools
            {
                "name": "Speech to Text",
                "description": "Convert speech audio to text",
                "category": "Audio Processing",
                "provider": "Whisper",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "enum": ["tiny", "base", "small", "medium", "large"],
                            "default": "base"
                        },
                        "language": {
                            "type": "string",
                            "default": "auto"
                        }
                    }
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "audio": {
                            "type": "string",
                            "description": "Base64 encoded audio file or audio URL"
                        }
                    },
                    "required": ["audio"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Transcribed text"
                        },
                        "language": {
                            "type": "string",
                            "description": "Detected language"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Transcription confidence"
                        }
                    }
                }
            },
            {
                "name": "Text to Speech",
                "description": "Convert text to speech audio",
                "category": "Audio Processing",
                "provider": "ElevenLabs",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "voice": {
                            "type": "string",
                            "default": "alloy"
                        },
                        "model": {
                            "type": "string",
                            "default": "eleven_monolingual_v1"
                        }
                    }
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to convert to speech"
                        }
                    },
                    "required": ["text"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "audio_url": {
                            "type": "string",
                            "description": "URL of generated audio file"
                        },
                        "duration": {
                            "type": "number",
                            "description": "Audio duration in seconds"
                        }
                    }
                }
            }
        ]
    
    def initialize_marketplace(self):
        """Initialize the marketplace with predefined tools"""
        for tool_data in self.predefined_tools:
            # Check if tool already exists
            existing_tool = self.db.query(AITool).filter(
                AITool.name == tool_data["name"]
            ).first()
            
            if not existing_tool:
                tool = AITool(
                    id=str(uuid.uuid4()),
                    name=tool_data["name"],
                    description=tool_data["description"],
                    category=tool_data["category"],
                    provider=tool_data["provider"],
                    config_schema=tool_data["config_schema"],
                    input_schema=tool_data["input_schema"],
                    output_schema=tool_data["output_schema"],
                    is_active=True
                )
                
                self.db.add(tool)
                logger.info(f"Added AI tool: {tool_data['name']}")
        
        self.db.commit()
        logger.info("AI Tools Marketplace initialized")
    
    def get_tools_by_category(self, category: str) -> List[AITool]:
        """Get tools by category"""
        return self.db.query(AITool).filter(
            and_(
                AITool.category == category,
                AITool.is_active == True
            )
        ).all()
    
    def get_tools_by_provider(self, provider: str) -> List[AITool]:
        """Get tools by provider"""
        return self.db.query(AITool).filter(
            and_(
                AITool.provider == provider,
                AITool.is_active == True
            )
        ).all()
    
    def search_tools(self, query: str) -> List[AITool]:
        """Search tools by name or description"""
        return self.db.query(AITool).filter(
            and_(
                AITool.is_active == True,
                (AITool.name.ilike(f"%{query}%") | AITool.description.ilike(f"%{query}%"))
            )
        ).all()
    
    def get_popular_tools(self, limit: int = 10) -> List[AITool]:
        """Get popular tools (could be based on usage statistics)"""
        return self.db.query(AITool).filter(
            AITool.is_active == True
        ).limit(limit).all()
    
    def get_tool_categories(self) -> List[str]:
        """Get all available tool categories"""
        categories = self.db.query(AITool.category).filter(
            AITool.is_active == True
        ).distinct().all()
        
        return [category[0] for category in categories]
    
    def get_tool_providers(self) -> List[str]:
        """Get all available tool providers"""
        providers = self.db.query(AITool.provider).filter(
            AITool.is_active == True
        ).distinct().all()
        
        return [provider[0] for provider in providers]
    
    def create_custom_tool(self, tool_data: AIToolCreate, user: User) -> AITool:
        """Create a custom AI tool"""
        # Check if user has permission to create tools
        if not user.is_admin:
            raise ValueError("Only admins can create custom tools")
        
        tool = AITool(
            id=str(uuid.uuid4()),
            name=tool_data.name,
            description=tool_data.description,
            category=tool_data.category,
            provider=tool_data.provider,
            config_schema=tool_data.config_schema,
            input_schema=tool_data.input_schema,
            output_schema=tool_data.output_schema,
            is_active=True
        )
        
        self.db.add(tool)
        self.db.commit()
        self.db.refresh(tool)
        
        logger.info(f"Created custom AI tool: {tool_data.name}")
        return tool
    
    def update_tool(self, tool_id: str, tool_data: AIToolUpdate, user: User) -> AITool:
        """Update an AI tool"""
        tool = self.db.query(AITool).filter(AITool.id == tool_id).first()
        
        if not tool:
            raise ValueError("Tool not found")
        
        # Check permissions
        if not user.is_admin:
            raise ValueError("Only admins can update tools")
        
        # Update fields
        for field, value in tool_data.dict(exclude_unset=True).items():
            setattr(tool, field, value)
        
        tool.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(tool)
        
        logger.info(f"Updated AI tool: {tool.name}")
        return tool
    
    def deactivate_tool(self, tool_id: str, user: User) -> bool:
        """Deactivate an AI tool"""
        tool = self.db.query(AITool).filter(AITool.id == tool_id).first()
        
        if not tool:
            raise ValueError("Tool not found")
        
        # Check permissions
        if not user.is_admin:
            raise ValueError("Only admins can deactivate tools")
        
        tool.is_active = False
        tool.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"Deactivated AI tool: {tool.name}")
        return True
    
    def get_tool_usage_stats(self, tool_id: str) -> Dict[str, Any]:
        """Get usage statistics for a tool"""
        # This would integrate with actual usage tracking
        # For now, return mock data
        return {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "average_duration": 0.0,
            "last_used": None
        }
    
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics"""
        total_tools = self.db.query(AITool).filter(AITool.is_active == True).count()
        categories = len(self.get_tool_categories())
        providers = len(self.get_tool_providers())
        
        return {
            "total_tools": total_tools,
            "categories": categories,
            "providers": providers,
            "last_updated": datetime.utcnow().isoformat()
        }
