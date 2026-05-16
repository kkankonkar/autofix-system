"""Classify PR changes as major (needs docs) or minor (skip docs)."""
from enum import Enum
from typing import Dict, List, Optional


class ChangeType(Enum):
    """Types of changes in a PR."""
    MAJOR_FEATURE = "major_feature"
    SIGNIFICANT_UPDATE = "significant_update"
    MINOR_CHANGE = "minor_change"
    UNCERTAIN = "uncertain"


class ChangeClassifier:
    """Analyze PR changes to determine if documentation updates needed."""
    
    # Keywords in commit messages indicating major changes
    MAJOR_KEYWORDS = [
        'feat:', 'feature:', 'add:', 'new:', 'breaking:', 
        'deprecate:', 'remove:', 'change:', 'introduce:',
        'implement:', 'create:'
    ]
    
    # Keywords in commit messages indicating minor changes
    MINOR_KEYWORDS = [
        'fix:', 'patch:', 'chore:', 'deps:', 'security:',
        'refactor:', 'perf:', 'test:', 'style:', 'docs:',
        'build:', 'ci:', 'revert:'
    ]
    
    # File patterns that indicate major changes
    MAJOR_FILE_PATTERNS = [
        'src/', 'lib/', 'app/', 'api/', 'core/',
        'services/', 'controllers/', 'routes/',
        'handlers/', 'middleware/'
    ]
    
    # File patterns that indicate minor changes
    MINOR_FILE_PATTERNS = [
        'test/', 'tests/', '__tests__/', 'spec/',
        '.github/', '.gitlab/', 'scripts/',
        'package.json', 'package-lock.json',
        'requirements.txt', 'Pipfile', 'Pipfile.lock',
        'Cargo.toml', 'Cargo.lock', 'go.mod', 'go.sum',
        'yarn.lock', 'pnpm-lock.yaml'
    ]
    
    def classify_pr(
        self, 
        pr_files: List[str], 
        commit_messages: List[str],
        pr_title: Optional[str] = None
    ) -> Dict:
        """
        Classify PR changes to determine if documentation analysis needed.
        
        Args:
            pr_files: List of file paths changed in PR
            commit_messages: List of commit messages
            pr_title: Optional PR title
            
        Returns:
            {
                'classification': ChangeType,
                'confidence': str ('high', 'medium', 'low'),
                'reasons': list[str],
                'major_changes': list[dict],
                'should_analyze_docs': bool
            }
        """
        reasons = []
        major_changes = []
        confidence_score = 0
        
        # Analyze commit messages
        major_keyword_count = 0
        minor_keyword_count = 0
        
        all_messages = commit_messages.copy()
        if pr_title:
            all_messages.insert(0, pr_title)
        
        for msg in all_messages:
            msg_lower = msg.lower()
            
            # Check for major keywords
            for keyword in self.MAJOR_KEYWORDS:
                if keyword in msg_lower:
                    major_keyword_count += 1
                    reasons.append(f"Commit message contains '{keyword}': {msg[:60]}...")
                    confidence_score += 2
                    break
            
            # Check for minor keywords
            for keyword in self.MINOR_KEYWORDS:
                if keyword in msg_lower:
                    minor_keyword_count += 1
                    break
        
        # Analyze file changes
        source_files = []
        test_files = []
        config_files = []
        
        for file_path in pr_files:
            change_info = self.analyze_file_changes(file_path)
            
            if change_info['is_major']:
                major_changes.append(change_info)
                source_files.append(file_path)
                confidence_score += 1
            elif change_info['type'] == 'test':
                test_files.append(file_path)
            elif change_info['type'] == 'config':
                config_files.append(file_path)
        
        # Add reasons for file changes
        if source_files:
            reasons.append(f"Modified {len(source_files)} source file(s): {', '.join(source_files[:3])}")
        
        if test_files and not source_files:
            reasons.append(f"Only test files modified ({len(test_files)} file(s))")
            confidence_score -= 2
        
        if config_files and not source_files:
            reasons.append(f"Only configuration files modified ({len(config_files)} file(s))")
            confidence_score -= 2
        
        # Determine classification
        classification = self._determine_classification(
            major_keyword_count,
            minor_keyword_count,
            len(major_changes),
            len(test_files),
            len(config_files)
        )
        
        # Determine confidence
        if confidence_score >= 3:
            confidence = 'high'
        elif confidence_score >= 1:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        # Decide if documentation analysis needed
        should_analyze = classification in [
            ChangeType.MAJOR_FEATURE,
            ChangeType.SIGNIFICANT_UPDATE,
            ChangeType.UNCERTAIN
        ]
        
        # Add summary reason
        if not should_analyze:
            reasons.append("Changes are minor (bug fixes, tests, or dependency updates)")
        
        return {
            'classification': classification,
            'confidence': confidence,
            'reasons': reasons if reasons else ['No specific indicators found'],
            'major_changes': major_changes,
            'should_analyze_docs': should_analyze,
            'stats': {
                'source_files': len(source_files),
                'test_files': len(test_files),
                'config_files': len(config_files),
                'major_keywords': major_keyword_count,
                'minor_keywords': minor_keyword_count
            }
        }
    
    def _determine_classification(
        self,
        major_keyword_count: int,
        minor_keyword_count: int,
        major_file_count: int,
        test_file_count: int,
        config_file_count: int
    ) -> ChangeType:
        """
        Determine the change classification based on analysis.
        
        Args:
            major_keyword_count: Number of major keywords found
            minor_keyword_count: Number of minor keywords found
            major_file_count: Number of major files changed
            test_file_count: Number of test files changed
            config_file_count: Number of config files changed
            
        Returns:
            ChangeType enum value
        """
        # Only test or config files changed
        if major_file_count == 0 and (test_file_count > 0 or config_file_count > 0):
            return ChangeType.MINOR_CHANGE
        
        # Strong indicators of major changes
        if major_keyword_count > 0 and major_file_count > 0:
            return ChangeType.MAJOR_FEATURE
        
        # Only minor keywords and no major files
        if minor_keyword_count > 0 and major_file_count == 0:
            return ChangeType.MINOR_CHANGE
        
        # Major files changed but no clear keywords
        if major_file_count > 0:
            if minor_keyword_count > major_keyword_count:
                return ChangeType.MINOR_CHANGE
            return ChangeType.SIGNIFICANT_UPDATE
        
        # Uncertain - err on side of caution
        return ChangeType.UNCERTAIN
    
    def analyze_file_changes(self, file_path: str) -> Dict:
        """
        Analyze individual file for major changes.
        
        Args:
            file_path: Path to file
            
        Returns:
            {
                'file': str,
                'is_major': bool,
                'type': str,
                'description': str
            }
        """
        file_lower = file_path.lower()
        
        # Check if it's a test file
        if any(pattern in file_lower for pattern in ['test/', 'tests/', '__tests__/', 'spec/', '_test.', '.test.', '.spec.']):
            return {
                'file': file_path,
                'is_major': False,
                'type': 'test',
                'description': 'Test file'
            }
        
        # Check if it's a config/dependency file
        if any(file_path.endswith(pattern) or pattern in file_path for pattern in self.MINOR_FILE_PATTERNS):
            return {
                'file': file_path,
                'is_major': False,
                'type': 'config',
                'description': 'Configuration or dependency file'
            }
        
        # Check if it's a documentation file
        if file_path.endswith('.md') or 'docs/' in file_lower:
            return {
                'file': file_path,
                'is_major': False,
                'type': 'documentation',
                'description': 'Documentation file'
            }
        
        # Check if it's a source file
        if any(file_path.startswith(pattern) for pattern in self.MAJOR_FILE_PATTERNS):
            return {
                'file': file_path,
                'is_major': True,
                'type': 'source',
                'description': 'Source code file'
            }
        
        # Check by file extension
        source_extensions = ['.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.c', '.rb', '.php']
        if any(file_path.endswith(ext) for ext in source_extensions):
            return {
                'file': file_path,
                'is_major': True,
                'type': 'source',
                'description': 'Source code file'
            }
        
        # Unknown file type - treat as potentially major
        return {
            'file': file_path,
            'is_major': False,
            'type': 'other',
            'description': 'Other file type'
        }
    
    def get_classification_summary(self, classification_result: Dict) -> str:
        """
        Generate human-readable summary of classification.
        
        Args:
            classification_result: Result from classify_pr()
            
        Returns:
            Formatted summary string
        """
        lines = []
        lines.append(f"**Classification**: {classification_result['classification'].value}")
        lines.append(f"**Confidence**: {classification_result['confidence']}")
        lines.append(f"**Should Analyze Docs**: {'Yes' if classification_result['should_analyze_docs'] else 'No'}")
        
        stats = classification_result['stats']
        lines.append(f"\n**File Statistics**:")
        lines.append(f"  - Source files: {stats['source_files']}")
        lines.append(f"  - Test files: {stats['test_files']}")
        lines.append(f"  - Config files: {stats['config_files']}")
        
        lines.append(f"\n**Reasons**:")
        for reason in classification_result['reasons']:
            lines.append(f"  - {reason}")
        
        return "\n".join(lines)


# Made with Bob