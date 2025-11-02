import os
import glob
from typing import Dict, List, Optional
from pathlib import Path
import markdown
import frontmatter

class PromptsRepository:
    """Repository for managing prompt presets stored as Markdown files."""

    def __init__(self, prompts_dir: str = "data/prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(exist_ok=True)

    def list_prompts(self) -> List[Dict[str, str]]:
        """List all available prompts with metadata."""
        prompts = []
        for md_file in self.prompts_dir.glob("*.md"):
            try:
                post = frontmatter.load(md_file)
                prompts.append({
                    'id': post.get('id', md_file.stem),
                    'title': post.get('title', md_file.stem),
                    'category': post.get('category', 'General'),
                    'tags': post.get('tags', []),
                    'filename': md_file.name,
                    'updated_at': post.get('updated_at', '')
                })
            except Exception:
                # Skip invalid files
                continue
        return sorted(prompts, key=lambda x: x['title'])

    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, str]]:
        """Get a specific prompt by ID."""
        for md_file in self.prompts_dir.glob("*.md"):
            try:
                post = frontmatter.load(md_file)
                if post.get('id') == prompt_id or md_file.stem == prompt_id:
                    return {
                        'id': post.get('id', md_file.stem),
                        'title': post.get('title', md_file.stem),
                        'category': post.get('category', 'General'),
                        'tags': post.get('tags', []),
                        'content': post.content,
                        'filename': md_file.name
                    }
            except Exception:
                continue
        return None

    def save_prompt(self, prompt_data: Dict[str, str]) -> bool:
        """Save a prompt to a Markdown file."""
        try:
            # Create frontmatter
            metadata = {
                'id': prompt_data.get('id', prompt_data['title'].lower().replace(' ', '-')),
                'title': prompt_data['title'],
                'category': prompt_data.get('category', 'General'),
                'tags': prompt_data.get('tags', []),
                'version': prompt_data.get('version', '1.0.0'),
                'updated_at': prompt_data.get('updated_at', '')
            }

            # Create post
            post = frontmatter.Post(prompt_data['content'], **metadata)

            # Generate filename
            filename = f"{metadata['id']}.md"
            filepath = self.prompts_dir / filename

            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            return True
        except Exception:
            return False

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt by ID."""
        for md_file in self.prompts_dir.glob("*.md"):
            try:
                post = frontmatter.load(md_file)
                if post.get('id') == prompt_id or md_file.stem == prompt_id:
                    md_file.unlink()
                    return True
            except Exception:
                continue
        return False