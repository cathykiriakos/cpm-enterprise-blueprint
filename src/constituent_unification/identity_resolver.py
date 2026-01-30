"""
Constituent Unification Engine
==============================

Probabilistic and deterministic identity resolution to create
unified constituent records from disparate source systems.

This module implements:
1. Deterministic matching (exact email, phone)
2. Probabilistic matching (fuzzy name, address)
3. Conflict resolution for merged records
4. Full audit trail of match decisions

Author: Catherine Kiriakos
"""

import re
import uuid
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set, Any
from datetime import datetime
from enum import Enum
import logging

# Third-party imports (with fallbacks for demo)
try:
    from jellyfish import jaro_winkler_similarity
except ImportError:
    # Fallback implementation
    def jaro_winkler_similarity(s1: str, s2: str) -> float:
        """Simple Jaro-Winkler approximation for demo purposes."""
        if s1 == s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        s1, s2 = s1.lower(), s2.lower()
        
        # Simple character overlap ratio
        common = set(s1) & set(s2)
        if not common:
            return 0.0
        
        matches = sum(1 for c in s1 if c in common)
        return matches / max(len(s1), len(s2))


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of identity matches."""
    DETERMINISTIC_EMAIL = "deterministic_email"
    DETERMINISTIC_PHONE = "deterministic_phone"
    PROBABILISTIC = "probabilistic"
    MANUAL_REVIEW = "manual_review"
    NO_MATCH = "no_match"


@dataclass
class MatchConfig:
    """Configuration for identity matching thresholds."""
    
    # Deterministic matching
    generic_emails: Set[str] = field(default_factory=lambda: {
        "info@", "admin@", "support@", "contact@", "hello@",
        "noreply@", "no-reply@", "webmaster@", "postmaster@"
    })
    
    # Probabilistic thresholds
    auto_match_threshold: float = 0.85  # Auto-approve matches above this
    review_threshold: float = 0.70  # Send to review queue between review and auto
    
    # Feature weights for probabilistic scoring
    name_weight: float = 0.35
    address_weight: float = 0.30
    phone_weight: float = 0.15
    email_domain_weight: float = 0.10
    zip_weight: float = 0.10
    
    # Conflict resolution preferences
    prefer_most_recent: bool = True
    prefer_longest_name: bool = True


@dataclass
class SourceRecord:
    """A record from a source system."""
    
    source_system: str
    source_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Normalize fields after initialization."""
        if self.email:
            self.email = self.email.lower().strip()
        if self.phone:
            self.phone = self._normalize_phone(self.phone)
        if self.first_name:
            self.first_name = self.first_name.strip()
        if self.last_name:
            self.last_name = self.last_name.strip()
        if self.full_name:
            self.full_name = self.full_name.strip()
        if self.zip_code:
            self.zip_code = self.zip_code[:5] if len(self.zip_code) >= 5 else self.zip_code
    
    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Extract digits from phone number."""
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 11 and digits[0] == '1':
            digits = digits[1:]
        return digits if len(digits) == 10 else phone
    
    @property
    def record_key(self) -> str:
        """Unique key for this source record."""
        return f"{self.source_system}:{self.source_id}"


@dataclass
class MatchResult:
    """Result of comparing two records."""
    
    record_a: SourceRecord
    record_b: SourceRecord
    match_type: MatchType
    confidence: float
    feature_scores: Dict[str, float] = field(default_factory=dict)
    match_reasons: List[str] = field(default_factory=list)
    matched_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "record_a_key": self.record_a.record_key,
            "record_b_key": self.record_b.record_key,
            "match_type": self.match_type.value,
            "confidence": self.confidence,
            "feature_scores": self.feature_scores,
            "match_reasons": self.match_reasons,
            "matched_at": self.matched_at.isoformat(),
        }


@dataclass
class UnifiedConstituent:
    """A unified constituent record (golden record)."""
    
    constituent_id: str
    canonical_email: Optional[str] = None
    canonical_first_name: Optional[str] = None
    canonical_last_name: Optional[str] = None
    canonical_phone: Optional[str] = None
    canonical_address_line1: Optional[str] = None
    canonical_city: Optional[str] = None
    canonical_state: Optional[str] = None
    canonical_zip: Optional[str] = None
    
    source_records: List[SourceRecord] = field(default_factory=list)
    match_history: List[MatchResult] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "constituent_id": self.constituent_id,
            "canonical_email": self.canonical_email,
            "canonical_first_name": self.canonical_first_name,
            "canonical_last_name": self.canonical_last_name,
            "canonical_phone": self.canonical_phone,
            "canonical_address_line1": self.canonical_address_line1,
            "canonical_city": self.canonical_city,
            "canonical_state": self.canonical_state,
            "canonical_zip": self.canonical_zip,
            "source_record_keys": [r.record_key for r in self.source_records],
            "source_systems": list(set(r.source_system for r in self.source_records)),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class IdentityResolver:
    """
    Main identity resolution engine.
    
    Implements a two-phase matching approach:
    1. Deterministic: Exact matches on email or phone
    2. Probabilistic: Fuzzy matching on name, address, etc.
    """
    
    def __init__(self, config: Optional[MatchConfig] = None):
        self.config = config or MatchConfig()
        self.match_log: List[MatchResult] = []
        self._email_index: Dict[str, List[SourceRecord]] = {}
        self._phone_index: Dict[str, List[SourceRecord]] = {}
        
    def _is_generic_email(self, email: str) -> bool:
        """Check if email is a generic/shared email."""
        if not email:
            return True
        for generic in self.config.generic_emails:
            if email.lower().startswith(generic):
                return True
        return False
    
    def _extract_name_parts(self, record: SourceRecord) -> Tuple[str, str]:
        """Extract first and last name from record."""
        if record.first_name and record.last_name:
            return record.first_name.lower(), record.last_name.lower()
        
        if record.full_name:
            parts = record.full_name.strip().split()
            if len(parts) >= 2:
                return parts[0].lower(), parts[-1].lower()
            elif len(parts) == 1:
                return parts[0].lower(), ""
        
        return "", ""
    
    def _calculate_name_similarity(
        self, 
        record_a: SourceRecord, 
        record_b: SourceRecord
    ) -> float:
        """Calculate name similarity score."""
        first_a, last_a = self._extract_name_parts(record_a)
        first_b, last_b = self._extract_name_parts(record_b)
        
        if not (first_a or last_a) or not (first_b or last_b):
            return 0.0
        
        # Compare first names
        first_sim = jaro_winkler_similarity(first_a, first_b) if first_a and first_b else 0.0
        
        # Compare last names (weighted higher)
        last_sim = jaro_winkler_similarity(last_a, last_b) if last_a and last_b else 0.0
        
        # Combined score (last name matters more)
        return first_sim * 0.4 + last_sim * 0.6
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for comparison."""
        if not address:
            return ""
        
        address = address.lower().strip()
        
        # Standard abbreviations
        replacements = [
            (r'\bstreet\b', 'st'),
            (r'\bstr\b', 'st'),
            (r'\bavenue\b', 'ave'),
            (r'\bav\b', 'ave'),
            (r'\broad\b', 'rd'),
            (r'\bdrive\b', 'dr'),
            (r'\bboulevard\b', 'blvd'),
            (r'\blane\b', 'ln'),
            (r'\bcourt\b', 'ct'),
            (r'\bapartment\b', 'apt'),
            (r'\bunit\b', 'apt'),
            (r'\bsuite\b', 'ste'),
            (r'\bnorth\b', 'n'),
            (r'\bsouth\b', 's'),
            (r'\beast\b', 'e'),
            (r'\bwest\b', 'w'),
            (r'[,.]', ''),
            (r'\s+', ' '),
        ]
        
        for pattern, replacement in replacements:
            address = re.sub(pattern, replacement, address)
        
        return address.strip()
    
    def _calculate_address_similarity(
        self, 
        record_a: SourceRecord, 
        record_b: SourceRecord
    ) -> float:
        """Calculate address similarity score."""
        addr_a = self._normalize_address(record_a.address_line1)
        addr_b = self._normalize_address(record_b.address_line1)
        
        if not addr_a or not addr_b:
            return 0.0
        
        return jaro_winkler_similarity(addr_a, addr_b)
    
    def _calculate_phone_similarity(
        self, 
        record_a: SourceRecord, 
        record_b: SourceRecord
    ) -> float:
        """Calculate phone similarity score."""
        if not record_a.phone or not record_b.phone:
            return 0.0
        
        # Exact match after normalization
        if record_a.phone == record_b.phone:
            return 1.0
        
        # Partial match (last 7 digits)
        if len(record_a.phone) >= 7 and len(record_b.phone) >= 7:
            if record_a.phone[-7:] == record_b.phone[-7:]:
                return 0.8
        
        return 0.0
    
    def _calculate_email_domain_similarity(
        self, 
        record_a: SourceRecord, 
        record_b: SourceRecord
    ) -> float:
        """Check if emails share the same domain."""
        if not record_a.email or not record_b.email:
            return 0.0
        
        domain_a = record_a.email.split('@')[-1] if '@' in record_a.email else ""
        domain_b = record_b.email.split('@')[-1] if '@' in record_b.email else ""
        
        if domain_a and domain_a == domain_b:
            return 1.0
        
        return 0.0
    
    def _calculate_zip_similarity(
        self, 
        record_a: SourceRecord, 
        record_b: SourceRecord
    ) -> float:
        """Check if zip codes match."""
        if not record_a.zip_code or not record_b.zip_code:
            return 0.0
        
        # Exact 5-digit match
        if record_a.zip_code[:5] == record_b.zip_code[:5]:
            return 1.0
        
        # Same 3-digit prefix (same general area)
        if record_a.zip_code[:3] == record_b.zip_code[:3]:
            return 0.5
        
        return 0.0
    
    def compare_records(
        self, 
        record_a: SourceRecord, 
        record_b: SourceRecord
    ) -> MatchResult:
        """
        Compare two records and determine if they match.
        
        Returns a MatchResult with confidence score and match type.
        """
        match_reasons = []
        
        # Phase 1: Deterministic matching
        
        # Email exact match (highest confidence)
        if (record_a.email and record_b.email and 
            record_a.email == record_b.email and
            not self._is_generic_email(record_a.email)):
            
            return MatchResult(
                record_a=record_a,
                record_b=record_b,
                match_type=MatchType.DETERMINISTIC_EMAIL,
                confidence=1.0,
                feature_scores={"email_exact": 1.0},
                match_reasons=["Exact email match"]
            )
        
        # Phone exact match
        if (record_a.phone and record_b.phone and
            record_a.phone == record_b.phone and
            len(record_a.phone) >= 10):
            
            return MatchResult(
                record_a=record_a,
                record_b=record_b,
                match_type=MatchType.DETERMINISTIC_PHONE,
                confidence=0.95,
                feature_scores={"phone_exact": 1.0},
                match_reasons=["Exact phone match"]
            )
        
        # Phase 2: Probabilistic matching
        
        # Calculate feature scores
        name_score = self._calculate_name_similarity(record_a, record_b)
        address_score = self._calculate_address_similarity(record_a, record_b)
        phone_score = self._calculate_phone_similarity(record_a, record_b)
        email_domain_score = self._calculate_email_domain_similarity(record_a, record_b)
        zip_score = self._calculate_zip_similarity(record_a, record_b)
        
        feature_scores = {
            "name_similarity": name_score,
            "address_similarity": address_score,
            "phone_similarity": phone_score,
            "email_domain": email_domain_score,
            "zip_match": zip_score,
        }
        
        # Calculate weighted confidence
        confidence = (
            name_score * self.config.name_weight +
            address_score * self.config.address_weight +
            phone_score * self.config.phone_weight +
            email_domain_score * self.config.email_domain_weight +
            zip_score * self.config.zip_weight
        )
        
        # Build match reasons
        if name_score > 0.8:
            match_reasons.append(f"Strong name match ({name_score:.2f})")
        elif name_score > 0.6:
            match_reasons.append(f"Moderate name match ({name_score:.2f})")
        
        if address_score > 0.8:
            match_reasons.append(f"Strong address match ({address_score:.2f})")
        elif address_score > 0.6:
            match_reasons.append(f"Moderate address match ({address_score:.2f})")
        
        if phone_score > 0:
            match_reasons.append(f"Phone match ({phone_score:.2f})")
        
        if zip_score == 1.0:
            match_reasons.append("Same zip code")
        
        # Determine match type based on confidence
        if confidence >= self.config.auto_match_threshold:
            match_type = MatchType.PROBABILISTIC
        elif confidence >= self.config.review_threshold:
            match_type = MatchType.MANUAL_REVIEW
        else:
            match_type = MatchType.NO_MATCH
        
        return MatchResult(
            record_a=record_a,
            record_b=record_b,
            match_type=match_type,
            confidence=confidence,
            feature_scores=feature_scores,
            match_reasons=match_reasons
        )
    
    def build_indices(self, records: List[SourceRecord]) -> None:
        """Build lookup indices for efficient matching."""
        self._email_index.clear()
        self._phone_index.clear()
        
        for record in records:
            if record.email and not self._is_generic_email(record.email):
                if record.email not in self._email_index:
                    self._email_index[record.email] = []
                self._email_index[record.email].append(record)
            
            if record.phone and len(record.phone) >= 10:
                if record.phone not in self._phone_index:
                    self._phone_index[record.phone] = []
                self._phone_index[record.phone].append(record)
    
    def find_matches(
        self, 
        record: SourceRecord,
        candidates: Optional[List[SourceRecord]] = None
    ) -> List[MatchResult]:
        """
        Find all matching records for a given record.
        
        Uses indices for deterministic matches, then falls back
        to comparing against candidates for probabilistic matches.
        """
        matches = []
        compared = set()
        
        # Check email index for deterministic matches
        if record.email and record.email in self._email_index:
            for candidate in self._email_index[record.email]:
                if candidate.record_key != record.record_key:
                    result = self.compare_records(record, candidate)
                    if result.match_type != MatchType.NO_MATCH:
                        matches.append(result)
                    compared.add(candidate.record_key)
        
        # Check phone index for deterministic matches
        if record.phone and record.phone in self._phone_index:
            for candidate in self._phone_index[record.phone]:
                if (candidate.record_key != record.record_key and 
                    candidate.record_key not in compared):
                    result = self.compare_records(record, candidate)
                    if result.match_type != MatchType.NO_MATCH:
                        matches.append(result)
                    compared.add(candidate.record_key)
        
        # Probabilistic matching against remaining candidates
        if candidates:
            for candidate in candidates:
                if (candidate.record_key != record.record_key and
                    candidate.record_key not in compared):
                    result = self.compare_records(record, candidate)
                    if result.match_type != MatchType.NO_MATCH:
                        matches.append(result)
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return matches


class ConflictResolver:
    """
    Resolves conflicts when merging source records
    into a unified constituent record.
    """
    
    def __init__(self, config: Optional[MatchConfig] = None):
        self.config = config or MatchConfig()
    
    def resolve_email(self, records: List[SourceRecord]) -> Optional[str]:
        """Select canonical email from multiple records."""
        emails = [r.email for r in records if r.email]
        if not emails:
            return None
        
        # Prefer most recent if we have timestamps
        if self.config.prefer_most_recent:
            records_with_email = [r for r in records if r.email]
            records_with_timestamp = [r for r in records_with_email if r.updated_at]
            if records_with_timestamp:
                records_with_timestamp.sort(key=lambda x: x.updated_at, reverse=True)
                return records_with_timestamp[0].email
        
        # Otherwise, prefer non-generic email
        non_generic = [e for e in emails if not any(
            e.lower().startswith(g) for g in ["info@", "admin@", "support@"]
        )]
        if non_generic:
            return non_generic[0]
        
        return emails[0]
    
    def resolve_name(self, records: List[SourceRecord]) -> Tuple[Optional[str], Optional[str]]:
        """Select canonical name from multiple records."""
        first_names = []
        last_names = []
        
        for record in records:
            if record.first_name:
                first_names.append(record.first_name)
            if record.last_name:
                last_names.append(record.last_name)
            if record.full_name and not record.first_name:
                parts = record.full_name.strip().split()
                if len(parts) >= 2:
                    first_names.append(parts[0])
                    last_names.append(parts[-1])
        
        # Prefer longest version (most complete)
        canonical_first = max(first_names, key=len) if first_names else None
        canonical_last = max(last_names, key=len) if last_names else None
        
        return canonical_first, canonical_last
    
    def resolve_phone(self, records: List[SourceRecord]) -> Optional[str]:
        """Select canonical phone from multiple records."""
        phones = [r.phone for r in records if r.phone and len(r.phone) >= 10]
        if not phones:
            return None
        
        # Prefer most recent
        if self.config.prefer_most_recent:
            records_with_phone = [r for r in records if r.phone]
            records_with_timestamp = [r for r in records_with_phone if r.updated_at]
            if records_with_timestamp:
                records_with_timestamp.sort(key=lambda x: x.updated_at, reverse=True)
                return records_with_timestamp[0].phone
        
        return phones[0]
    
    def resolve_address(
        self, 
        records: List[SourceRecord]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Select canonical address from multiple records."""
        records_with_address = [r for r in records if r.address_line1]
        
        if not records_with_address:
            return None, None, None, None
        
        # Prefer most recent
        if self.config.prefer_most_recent:
            records_with_timestamp = [r for r in records_with_address if r.updated_at]
            if records_with_timestamp:
                records_with_timestamp.sort(key=lambda x: x.updated_at, reverse=True)
                r = records_with_timestamp[0]
                return r.address_line1, r.city, r.state, r.zip_code
        
        r = records_with_address[0]
        return r.address_line1, r.city, r.state, r.zip_code


class ConstituentUnifier:
    """
    Main class that orchestrates the full unification process.
    
    Takes records from multiple source systems and produces
    unified constituent records with full audit trail.
    """
    
    def __init__(self, config: Optional[MatchConfig] = None):
        self.config = config or MatchConfig()
        self.resolver = IdentityResolver(config)
        self.conflict_resolver = ConflictResolver(config)
        self.unified_constituents: Dict[str, UnifiedConstituent] = {}
        self.record_to_constituent: Dict[str, str] = {}  # Maps source record key to constituent ID
    
    def _generate_constituent_id(self) -> str:
        """Generate a new unique constituent ID."""
        return f"UC-{uuid.uuid4().hex[:12]}"
    
    def _create_unified_constituent(
        self, 
        records: List[SourceRecord],
        match_results: List[MatchResult]
    ) -> UnifiedConstituent:
        """Create a unified constituent from matched records."""
        constituent_id = self._generate_constituent_id()
        
        # Resolve conflicts for canonical values
        canonical_email = self.conflict_resolver.resolve_email(records)
        canonical_first, canonical_last = self.conflict_resolver.resolve_name(records)
        canonical_phone = self.conflict_resolver.resolve_phone(records)
        addr, city, state, zip_code = self.conflict_resolver.resolve_address(records)
        
        constituent = UnifiedConstituent(
            constituent_id=constituent_id,
            canonical_email=canonical_email,
            canonical_first_name=canonical_first,
            canonical_last_name=canonical_last,
            canonical_phone=canonical_phone,
            canonical_address_line1=addr,
            canonical_city=city,
            canonical_state=state,
            canonical_zip=zip_code,
            source_records=records,
            match_history=match_results,
        )
        
        return constituent
    
    def unify_records(
        self, 
        records: List[SourceRecord],
        enable_probabilistic: bool = True
    ) -> List[UnifiedConstituent]:
        """
        Main unification method.
        
        Takes a list of source records and returns unified constituents.
        
        Args:
            records: List of source records to unify
            enable_probabilistic: Whether to use probabilistic matching
                                  (disable for faster deterministic-only matching)
        
        Returns:
            List of unified constituent records
        """
        logger.info(f"Starting unification of {len(records)} records")
        
        # Build indices for efficient matching
        self.resolver.build_indices(records)
        
        # Track which records have been assigned to constituents
        unassigned = set(r.record_key for r in records)
        record_lookup = {r.record_key: r for r in records}
        
        # Phase 1: Find all matches
        logger.info("Phase 1: Finding matches...")
        all_matches: Dict[str, List[MatchResult]] = {}
        
        for record in records:
            candidates = records if enable_probabilistic else None
            matches = self.resolver.find_matches(record, candidates)
            if matches:
                all_matches[record.record_key] = matches
        
        # Phase 2: Group matched records into clusters
        logger.info("Phase 2: Clustering matched records...")
        
        # Union-Find for clustering
        parent = {r.record_key: r.record_key for r in records}
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # Union matched records
        for record_key, matches in all_matches.items():
            for match in matches:
                if match.match_type in (MatchType.DETERMINISTIC_EMAIL, 
                                         MatchType.DETERMINISTIC_PHONE,
                                         MatchType.PROBABILISTIC):
                    union(match.record_a.record_key, match.record_b.record_key)
        
        # Build clusters
        clusters: Dict[str, List[str]] = {}
        for record_key in parent:
            root = find(record_key)
            if root not in clusters:
                clusters[root] = []
            clusters[root].append(record_key)
        
        # Phase 3: Create unified constituents
        logger.info("Phase 3: Creating unified constituents...")
        unified_list = []
        
        for cluster_root, cluster_keys in clusters.items():
            cluster_records = [record_lookup[k] for k in cluster_keys]
            
            # Gather match results for this cluster
            cluster_matches = []
            for key in cluster_keys:
                if key in all_matches:
                    cluster_matches.extend(all_matches[key])
            
            # Deduplicate match results
            seen_pairs = set()
            unique_matches = []
            for match in cluster_matches:
                pair = tuple(sorted([match.record_a.record_key, match.record_b.record_key]))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    unique_matches.append(match)
            
            constituent = self._create_unified_constituent(cluster_records, unique_matches)
            unified_list.append(constituent)
            
            # Track mappings
            self.unified_constituents[constituent.constituent_id] = constituent
            for record in cluster_records:
                self.record_to_constituent[record.record_key] = constituent.constituent_id
        
        logger.info(f"Unification complete: {len(records)} records -> {len(unified_list)} constituents")
        
        # Log statistics
        multi_source = sum(1 for c in unified_list if len(set(r.source_system for r in c.source_records)) > 1)
        logger.info(f"  - {multi_source} constituents linked across multiple source systems")
        
        return unified_list
    
    def get_match_statistics(self) -> Dict[str, Any]:
        """Return statistics about the matching process."""
        if not self.unified_constituents:
            return {}
        
        constituents = list(self.unified_constituents.values())
        
        # Count by source record count
        record_count_dist = {}
        for c in constituents:
            count = len(c.source_records)
            record_count_dist[count] = record_count_dist.get(count, 0) + 1
        
        # Count by source system combinations
        source_combos = {}
        for c in constituents:
            sources = tuple(sorted(set(r.source_system for r in c.source_records)))
            source_combos[sources] = source_combos.get(sources, 0) + 1
        
        # Match type distribution
        match_types = {}
        for c in constituents:
            for match in c.match_history:
                mt = match.match_type.value
                match_types[mt] = match_types.get(mt, 0) + 1
        
        return {
            "total_constituents": len(constituents),
            "total_source_records": sum(len(c.source_records) for c in constituents),
            "avg_records_per_constituent": sum(len(c.source_records) for c in constituents) / len(constituents),
            "record_count_distribution": record_count_dist,
            "source_system_combinations": {str(k): v for k, v in source_combos.items()},
            "match_type_distribution": match_types,
        }


def load_records_from_csv(
    filepath: str,
    source_system: str,
    field_mapping: Dict[str, str]
) -> List[SourceRecord]:
    """
    Load source records from a CSV file.
    
    Args:
        filepath: Path to CSV file
        source_system: Name of the source system
        field_mapping: Maps SourceRecord field names to CSV column names
    
    Returns:
        List of SourceRecord objects
    """
    import csv
    
    records = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            record_data = {
                "source_system": source_system,
                "raw_data": dict(row),
            }
            
            for record_field, csv_column in field_mapping.items():
                if csv_column in row:
                    record_data[record_field] = row[csv_column]
            
            records.append(SourceRecord(**record_data))
    
    return records


# Example usage and testing
if __name__ == "__main__":
    # Create test records simulating cross-system data
    test_records = [
        # WBEZ donation record
        SourceRecord(
            source_system="wbez_donations",
            source_id="D-001",
            email="john.smith@gmail.com",
            first_name="John",
            last_name="Smith",
            phone="312-555-1234",
            address_line1="123 Main Street",
            city="Chicago",
            state="IL",
            zip_code="60601",
            created_at=datetime(2023, 1, 15)
        ),
        # Sun-Times subscription with slight variations
        SourceRecord(
            source_system="suntimes_subs",
            source_id="S-001",
            email="j.smith@work.com",  # Different email
            full_name="John M Smith",  # Middle initial
            phone="312-555-1234",  # Same phone
            address_line1="123 Main St",  # Abbreviated
            city="Chicago",
            state="IL",
            zip_code="60601",
            created_at=datetime(2023, 6, 20)
        ),
        # Event ticket with email match
        SourceRecord(
            source_system="events",
            source_id="E-001",
            email="john.smith@gmail.com",  # Same as WBEZ
            full_name="J. Smith",  # Initial only
            created_at=datetime(2024, 3, 10)
        ),
        # Different person
        SourceRecord(
            source_system="wbez_donations",
            source_id="D-002",
            email="mary.jones@gmail.com",
            first_name="Mary",
            last_name="Jones",
            address_line1="456 Oak Avenue",
            city="Evanston",
            state="IL",
            zip_code="60201",
            created_at=datetime(2023, 3, 1)
        ),
    ]
    
    # Run unification
    unifier = ConstituentUnifier()
    constituents = unifier.unify_records(test_records)
    
    # Print results
    print("\n" + "="*60)
    print("UNIFICATION RESULTS")
    print("="*60)
    
    for constituent in constituents:
        print(f"\nConstituent: {constituent.constituent_id}")
        print(f"  Canonical Name: {constituent.canonical_first_name} {constituent.canonical_last_name}")
        print(f"  Canonical Email: {constituent.canonical_email}")
        print(f"  Canonical Phone: {constituent.canonical_phone}")
        print(f"  Source Records: {len(constituent.source_records)}")
        for record in constituent.source_records:
            print(f"    - {record.source_system}: {record.source_id}")
        if constituent.match_history:
            print(f"  Matches:")
            for match in constituent.match_history:
                print(f"    - {match.match_type.value}: {match.confidence:.2f}")
                print(f"      Reasons: {', '.join(match.match_reasons)}")
    
    print("\n" + "="*60)
    print("STATISTICS")
    print("="*60)
    
    stats = unifier.get_match_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")