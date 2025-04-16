import httpx
from bs4 import BeautifulSoup
import re
from typing import Optional, List, Dict
import json
import os
import logging
from pathlib import Path
import time
from ..utils import create_retry_decorator, handle_source_error, NetworkError, SourceError

logger = logging.getLogger(__name__)

class CheatShSource:
    """A source that fetches cheat sheets from cheat.sh."""
    
    # Create retry decorator for network requests
    retry_request = create_retry_decorator(
        max_attempts=3,
        min_wait=1,
        max_wait=10
    )
    
    def __init__(self):
        """Initialize the CheatShSource."""
        self.base_url = "https://cheat.sh"
        self.topics_cache = {}
        self.client = httpx.Client(
            timeout=10.0,
            headers={
                "User-Agent": "curl/7.64.1",
                "Accept": "text/plain"
            },
            follow_redirects=True
        )
        self.cache_dir = Path.home() / '.pydevcheat' / 'cache' / 'cheatsh'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / 'topics.json'
        self.commands_cache = self.cache_dir / 'commands'
        self.commands_cache.mkdir(exist_ok=True)
        
        # Common programming topics to pre-cache
        self.common_topics = [
            'python', 'javascript', 'git', 'bash', 'docker',
            'kubernetes', 'react', 'node', 'sql', 'linux',
            'cpp', 'java', 'csharp', 'ruby', 'go', 'rust', 'php',
            'html', 'css', 'vue', 'angular', 'typescript',
            'mongodb', 'postgresql', 'mysql', 'redis',
            'nginx', 'apache', 'aws', 'azure', 'gcp'
        ]
    
    @retry_request
    def _make_request(self, url: str) -> str:
        """Make a retryable HTTP request."""
        response = self.client.get(url)
        response.raise_for_status()
        return response.text
    
    def search(self, query: str) -> Optional[str]:
        """
        Search cheat.sh for a given query and return formatted results.
        Returns None if no results found or error occurs.
        """
        try:
            # Clean up query
            query = query.lower().strip()
            
            # Try different URL patterns
            urls = []
            if '/' in query:
                base_query = query
            else:
                base_query = query.replace(' ', '+')
            
            # Try different formats
            urls.extend([
                f"{self.base_url}/{base_query}",
                f"{self.base_url}/{base_query}/:list",
                f"{self.base_url}/{base_query}?Q"
            ])
            
            content = None
            for url in urls:
                try:
                    content = self._make_request(url)
                    if content and not content.startswith("Unknown topic"):
                        break
                except Exception as e:
                    logger.warning(f"Failed to fetch {url}: {e}")
                    continue

            if not content or content.startswith("Unknown topic"):
                return None

            # Clean and format the content
            cleaned_content = self.clean_content(content)
            if not cleaned_content:
                return None
                
            return cleaned_content

        except Exception as e:
            handle_source_error("cheat.sh", e)
            return None
            
    def clean_content(self, content: str) -> str:
        """Clean and format the content from cheat.sh."""
        if not content:
            return ""

        # Split content into lines and initialize variables
        lines = content.splitlines()
        cleaned_lines = []
        in_code_block = False
        in_table = False
        table_lines = []
        
        # Add title header
        title = None
        
        for line in lines:
            # Remove ANSI color codes and special characters
            line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
            line = line.rstrip()

            # Skip unwanted metadata lines
            if any(skip in line.lower() for skip in ['cheat.sh', 'tldr.sh', 'curl cheat.sh']):
                continue
            
            # Extract title from first non-empty line if not set
            if not title and line.strip():
                title = line.strip().upper()
                cleaned_lines.append(f"# {title}\n")
                continue

            # Handle code blocks
            if line.startswith('```') or line.strip() == '---':
                in_code_block = not in_code_block
                if in_code_block:
                    cleaned_lines.append('\n```python')
                else:
                    cleaned_lines.append('```\n')
                continue

            # Handle tables
            if '|' in line and not in_code_block:
                if not in_table:
                    in_table = True
                    table_lines = []
                table_lines.append(line)
                continue
            elif in_table and not line.strip():
                in_table = False
                if table_lines:
                    formatted_table = self._format_table(table_lines)
                    cleaned_lines.extend(formatted_table)
                    table_lines = []
                continue

            # Handle section headers (all caps lines)
            if line.isupper() and len(line.strip()) > 0:
                cleaned_lines.append(f"\n## {line.title()}\n")
                continue

            # Handle performance metrics
            if any(metric in line.lower() for metric in ['μs', 'ns', 'loops', 'performance']):
                cleaned_lines.append(f"> {line.strip()}")
                continue

            # Handle regular lines
            if line.strip():
                if in_code_block:
                    # Preserve indentation in code blocks
                    cleaned_lines.append(line)
                else:
                    # Clean up regular text lines
                    cleaned_line = line.strip()
                    if cleaned_line:
                        cleaned_lines.append(cleaned_line)

        # Join lines and clean up multiple newlines
        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # Add a clean footer
        result += "\n\n---\nSource: cheat.sh"
        
        return result.strip()

    def _format_table(self, table_lines: List[str]) -> List[str]:
        """Format a table from the raw lines."""
        if not table_lines:
            return []

        # Clean up table lines and split into cells
        table_data = []
        max_cols = 0
        for line in table_lines:
            cells = [cell.strip() for cell in line.split('|')]
            cells = [cell for cell in cells if cell]  # Remove empty cells
            if cells:  # Only add non-empty rows
                table_data.append(cells)
                max_cols = max(max_cols, len(cells))

        if not table_data or max_cols == 0:
            return []

        # Ensure all rows have the same number of columns
        for row in table_data:
            while len(row) < max_cols:
                row.append('')

        # Calculate column widths
        col_widths = [0] * max_cols
        for row in table_data:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))

        # Format the table
        formatted_lines = []
        formatted_lines.append('')  # Add empty line before table

        # Header
        if table_data:
            # Header row
            header = '| ' + ' | '.join(cell.ljust(width) for cell, width in zip(table_data[0], col_widths)) + ' |'
            formatted_lines.append(header)
            
            # Separator with alignment indicators
            separator = '|'
            for width in col_widths:
                separator += ':' + '-' * (width) + ':|'
            formatted_lines.append(separator)

            # Data rows
            for row in table_data[1:]:
                formatted_row = '| ' + ' | '.join(cell.ljust(width) for cell, width in zip(row, col_widths)) + ' |'
                formatted_lines.append(formatted_row)

        formatted_lines.append('')  # Add empty line after table
        return formatted_lines

    def list_all_topics(self) -> Dict[str, str]:
        """List all available topics from cheat.sh organized by proper categories."""
        if self.topics_cache:
            return self.topics_cache
            
        try:
            url = f"{self.base_url}/:list"
            response = self.client.get(url)
            
            if response.status_code != 200:
                return self._get_fallback_topics()
                
            topics = {}
            current_category = "General"
            
            for line in response.text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Handle category headers from cheat.sh
                if line.startswith('#'):
                    current_category = line[1:].strip()
                    continue
                    
                # Skip special entries
                if line.startswith((':','.','/')) or line.startswith('cheat.sh'):
                    continue
                    
                # Clean up topic name and extract any category info
                parts = line.split('#', 1)
                topic = parts[0].strip().lower()
                
                # Skip invalid topics
                if not self._is_valid_topic(topic):
                    continue
                    
                # Determine the best category for this topic
                if len(parts) > 1 and parts[1].strip():
                    # Use provided category if available
                    category = parts[1].strip()
                else:
                    # Otherwise determine category from topic
                    category = self._determine_topic_category(topic, current_category)
                
                topics[topic] = category
            
            if not topics:
                return self._get_fallback_topics()
                
            self.topics_cache = topics
            return topics
                
        except Exception as e:
            logger.error(f"Error fetching topics from cheat.sh: {e}")
            return self._get_fallback_topics()
            
    def _is_valid_topic(self, topic: str) -> bool:
        """Check if a topic is valid and should be included."""
        if not topic or len(topic) < 2:
            return False
            
        # Skip special entries
        if topic.startswith((':','.','/')):
            return False
            
        # Skip version numbers and dates
        if re.match(r'^v?\d+(\.\d+)*$', topic):
            return False
            
        # Skip topics with invalid characters
        if re.search(r'[^a-z0-9\-_]', topic):
            return False
            
        return True

    def _determine_topic_category(self, topic: str, default_category: str) -> str:
        """Determine the most appropriate category for a topic."""
        # Define category mappings
        category_mappings = {
            # Programming Languages
            'python': 'Programming Languages',
            'javascript': 'Programming Languages',
            'typescript': 'Programming Languages',
            'java': 'Programming Languages',
            'cpp': 'Programming Languages',
            'c++': 'Programming Languages',
            'csharp': 'Programming Languages',
            'c#': 'Programming Languages',
            'go': 'Programming Languages',
            'rust': 'Programming Languages',
            'php': 'Programming Languages',
            'ruby': 'Programming Languages',
            'swift': 'Programming Languages',
            'kotlin': 'Programming Languages',
            
            # Web Development
            'html': 'Web Development',
            'css': 'Web Development',
            'react': 'Web Development',
            'vue': 'Web Development',
            'angular': 'Web Development',
            'node': 'Web Development',
            'npm': 'Web Development',
            'webpack': 'Web Development',
            'sass': 'Web Development',
            'django': 'Web Development',
            'flask': 'Web Development',
            
            # DevOps & Tools
            'git': 'Version Control',
            'docker': 'DevOps',
            'kubernetes': 'DevOps',
            'k8s': 'DevOps',
            'terraform': 'DevOps',
            'ansible': 'DevOps',
            'jenkins': 'DevOps',
            'nginx': 'DevOps',
            'apache': 'DevOps',
            
            # Cloud Platforms
            'aws': 'Cloud',
            'azure': 'Cloud',
            'gcp': 'Cloud',
            'heroku': 'Cloud',
            'digitalocean': 'Cloud',
            
            # Operating Systems
            'linux': 'Operating Systems',
            'ubuntu': 'Operating Systems',
            'debian': 'Operating Systems',
            'centos': 'Operating Systems',
            'windows': 'Operating Systems',
            'macos': 'Operating Systems',
            
            # Shell & CLI
            'bash': 'Shell & CLI',
            'zsh': 'Shell & CLI',
            'powershell': 'Shell & CLI',
            'ssh': 'Shell & CLI',
            'vim': 'Shell & CLI',
            'tmux': 'Shell & CLI',
            'curl': 'Shell & CLI',
            'wget': 'Shell & CLI',
            
            # Databases
            'sql': 'Databases',
            'mysql': 'Databases',
            'postgresql': 'Databases',
            'mongodb': 'Databases',
            'redis': 'Databases',
            'elasticsearch': 'Databases',
            
            # Data Science & ML
            'pandas': 'Data Science',
            'numpy': 'Data Science',
            'scipy': 'Data Science',
            'matplotlib': 'Data Science',
            'tensorflow': 'Machine Learning',
            'pytorch': 'Machine Learning',
            'scikit-learn': 'Machine Learning'
        }
        
        # Check direct matches
        if topic in category_mappings:
            return category_mappings[topic]
        
        # Check prefixes
        for key, category in category_mappings.items():
            if topic.startswith(f"{key}-") or topic.startswith(f"{key}_"):
                return category
        
        # Special cases for common prefixes
        if any(topic.startswith(prefix) for prefix in ['py', 'python']):
            return 'Python'
        if any(topic.startswith(prefix) for prefix in ['js', 'node']):
            return 'JavaScript'
        if topic.startswith('go'):
            return 'Go'
        if any(topic.startswith(prefix) for prefix in ['k8s', 'kube']):
            return 'Kubernetes'
        
        return default_category
    
    def _get_fallback_topics(self) -> Dict[str, str]:
        """Return a predefined list of common topics as fallback."""
        return {
            "python": "Programming",
            "javascript": "Programming",
            "java": "Programming",
            "c++": "Programming",
            "c#": "Programming",
            "ruby": "Programming",
            "php": "Programming",
            "go": "Programming",
            "rust": "Programming",
            "swift": "Programming",
            "kotlin": "Programming",
            "git": "Version Control",
            "docker": "DevOps",
            "kubernetes": "DevOps",
            "aws": "Cloud",
            "azure": "Cloud",
            "gcp": "Cloud",
            "linux": "Operating System",
            "windows": "Operating System",
            "macos": "Operating System",
            "bash": "Shell",
            "powershell": "Shell",
            "sql": "Database",
            "mongodb": "Database",
            "postgresql": "Database",
            "mysql": "Database",
            "redis": "Database",
            "nginx": "Web Server",
            "apache": "Web Server",
            "nodejs": "Web Development",
            "react": "Web Development",
            "vue": "Web Development",
            "angular": "Web Development",
            "django": "Web Development",
            "flask": "Web Development",
            "spring": "Web Development",
            "laravel": "Web Development",
            "rails": "Web Development",
            "tensorflow": "Machine Learning",
            "pytorch": "Machine Learning",
            "scikit-learn": "Machine Learning",
            "pandas": "Data Science",
            "numpy": "Data Science",
            "matplotlib": "Data Science",
            "seaborn": "Data Science",
            "jupyter": "Data Science",
            "vscode": "IDE",
            "vim": "Editor",
            "emacs": "Editor",
            "sublime": "Editor",
            "atom": "Editor",
            "intellij": "IDE",
            "eclipse": "IDE",
            "netbeans": "IDE",
            "android": "Mobile Development",
            "ios": "Mobile Development",
            "flutter": "Mobile Development",
            "react-native": "Mobile Development",
            "xamarin": "Mobile Development",
            "unity": "Game Development",
            "unreal": "Game Development",
            "godot": "Game Development",
            "blender": "3D Modeling",
            "maya": "3D Modeling",
            "3ds-max": "3D Modeling",
            "photoshop": "Design",
            "illustrator": "Design",
            "figma": "Design",
            "sketch": "Design",
            "invision": "Design",
            "adobe-xd": "Design",
            "premiere": "Video Editing",
            "after-effects": "Video Editing",
            "final-cut": "Video Editing",
            "davinci-resolve": "Video Editing",
            "audacity": "Audio Editing",
            "pro-tools": "Audio Editing",
            "logic-pro": "Audio Editing",
            "ableton": "Audio Editing",
            "fl-studio": "Audio Editing",
            "arduino": "Electronics",
            "raspberry-pi": "Electronics",
            "esp32": "Electronics",
            "esp8266": "Electronics",
            "stm32": "Electronics",
            "latex": "Documentation",
            "markdown": "Documentation",
            "asciidoc": "Documentation",
            "restructuredtext": "Documentation",
            "sphinx": "Documentation",
            "doxygen": "Documentation",
            "swagger": "API Documentation",
            "openapi": "API Documentation",
            "graphql": "API",
            "rest": "API",
            "soap": "API",
            "grpc": "API",
            "websocket": "API",
            "oauth": "Authentication",
            "jwt": "Authentication",
            "oauth2": "Authentication",
            "openid": "Authentication",
            "saml": "Authentication",
            "ldap": "Authentication",
            "kerberos": "Authentication",
            "ssl": "Security",
            "tls": "Security",
            "ssh": "Security",
            "pgp": "Security",
            "gpg": "Security",
            "encryption": "Security",
            "hashing": "Security",
            "jwt": "Security",
            "oauth": "Security",
            "oauth2": "Security",
            "openid": "Security",
            "saml": "Security",
            "ldap": "Security",
            "kerberos": "Security",
            "ssl": "Security",
            "tls": "Security",
            "ssh": "Security",
            "pgp": "Security",
            "gpg": "Security",
            "encryption": "Security",
            "hashing": "Security"
        }
    
    def _parse_response(self, content: str) -> str:
        """Parse cheat.sh response into a formatted string."""
        # Parse HTML content
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the pre element containing the cheat sheet content
        pre_element = soup.find('pre')
        if not pre_element:
            return "# Error: Could not parse cheat sheet content"
        
        # Extract and clean the content
        lines = pre_element.get_text().split('\n')
        result = []
        
        for line in lines:
            # Skip empty lines and navigation elements
            if not line.strip() or line.startswith('http'):
                continue
                
            # Remove ANSI color codes
            clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
            
            if clean_line.strip():
                result.append(clean_line)
        
        return '\n'.join(result)

    async def get_topics(self) -> List[str]:
        """Get list of available topics."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading cache: {e}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get('https://cheat.sh/:list')
                if response.status_code == 200:
                    topics = [line.strip() for line in response.text.split('\n') if line.strip()]
                    # Cache the topics
                    with open(self.cache_file, 'w') as f:
                        json.dump(topics, f)
                    return topics
        except Exception as e:
            logger.error(f"Error fetching topics: {e}")
            return []

    def is_synced(self) -> bool:
        """Check if the source is already synced."""
        try:
            # Check if cache directory exists
            if not self.cache_dir.exists():
                return False
                
            # Check if topics cache exists
            if not self.cache_file.exists():
                return False
                
            # Check if common topics are cached
            for topic in self.common_topics:
                cache_path = self.commands_cache / f'{topic}.txt'
                if not cache_path.exists():
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error checking sync status: {e}")
            return False

    def sync(self) -> bool:
        """Synchronize common commands locally."""
        try:
            # Create cache directory if it doesn't exist
            self.commands_cache.mkdir(parents=True, exist_ok=True)
            
            # First, get the list of all topics
            try:
                response = self.client.get(f'{self.base_url}/:list')
                if response.status_code == 200:
                    topics = []
                    for line in response.text.split('\n'):
                        line = line.strip()
                        if line and not line.startswith((':','#','/')):
                            # Clean up topic name
                            topic = line.split('#')[0].strip().lower()
                            if self._is_valid_topic(topic):
                                topics.append(topic)
                    
                    # Save all topics to cache
                    with open(self.cache_file, 'w') as f:
                        json.dump(topics, f)
                    
                    # Add top topics to common_topics if not already there
                    top_topics = [t for t in topics[:50] if self._is_valid_topic(t)]
                    self.common_topics.extend([t for t in top_topics if t not in self.common_topics])
            except Exception as e:
                logger.error(f"Error fetching topics list: {e}")
                # Continue with existing common_topics if fetch fails
            
            # Sync common topics with rate limiting
            for i, topic in enumerate(self.common_topics):
                try:
                    # Add a small delay every 5 requests to avoid rate limiting
                    if i > 0 and i % 5 == 0:
                        time.sleep(1)
                    
                    response = self.client.get(f'{self.base_url}/{topic}')
                    if response.status_code == 200:
                        cache_path = self.commands_cache / f'{topic}.txt'
                        with open(cache_path, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        logger.debug(f"Cached {topic}")
                except Exception as e:
                    logger.error(f"Error syncing {topic}: {e}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            return False

    async def get_command(self, topic: str, command: Optional[str] = None) -> str:
        """Get command details from cheat.sh."""
        cache_key = command if command else topic
        cache_path = self.commands_cache / f'{cache_key}.txt'
        
        # Check cache first
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
        
        # Fetch from API if not in cache
        try:
            url = f'https://cheat.sh/{topic}'
            if command:
                url = f'{url}/{command}'
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    content = response.text
                    # Cache the result
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return content
                else:
                    return f"Error: HTTP {response.status_code}"
        except Exception as e:
            logger.error(f"Error fetching command: {e}")
            return f"Error: {str(e)}" 