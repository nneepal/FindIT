from __future__ import annotations

import re
from dataclasses import dataclass

from .detection import detect_item_category
from .models import FoundItem, LostItem


STOPWORDS = {
    'a',
    'an',
    'and',
    'are',
    'bag',
    'blue',
    'book',
    'case',
    'color',
    'colour',
    'description',
    'found',
    'item',
    'lost',
    'my',
    'of',
    'or',
    'red',
    'the',
    'this',
    'with',
}


@dataclass
class MatchCandidate:
    item: FoundItem
    score: int
    reasons: list[str]
    detected_category: str
    detection_message: str


def _normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', ' ', (text or '').lower())).strip()


def _tokenize(text: str) -> set[str]:
    tokens = set()
    for token in _normalize_text(text).split():
        if len(token) < 3 or token in STOPWORDS:
            continue
        tokens.add(token)
    return tokens


def _item_text(item) -> str:
    parts = [item.item_name]
    if getattr(item, 'description', ''):
        parts.append(item.description)
    parts.append(getattr(item, 'get_category_display', lambda: '')())
    if hasattr(item, 'get_location_found_display'):
        parts.append(item.get_location_found_display())
    elif hasattr(item, 'get_location_lost_display'):
        parts.append(item.get_location_lost_display())
    return ' '.join(part for part in parts if part)


def _score_text_overlap(lost_item: LostItem, found_item: FoundItem) -> tuple[int, list[str]]:
    lost_tokens = _tokenize(_item_text(lost_item))
    found_tokens = _tokenize(_item_text(found_item))
    overlap = lost_tokens & found_tokens
    if not overlap:
        return 0, []

    bonus = min(len(overlap) * 7, 28)
    ordered_overlap = ', '.join(sorted(overlap)[:4])
    return bonus, [f'Text overlap: {ordered_overlap}']


def _detect_item_category_from_file(file_obj):
    if not file_obj:
        return {
            'raw_label': None,
            'confidence': 0.0,
            'category_value': 'other',
            'category_label': 'Other',
            'message': 'No image available for AI matching.',
        }
    return detect_item_category(file_obj)


def find_similar_found_items(lost_item: LostItem, limit: int = 8) -> dict:
    lost_detection = _detect_item_category_from_file(lost_item.image)
    lost_category = lost_detection.get('category_value') or 'other'
    lost_category_label = lost_detection.get('category_label') or 'Other'

    candidates = FoundItem.objects.select_related('reported_by').order_by('-updated_at', '-created_at')
    if lost_category != 'other':
        candidates = candidates.filter(category=lost_category)
    elif lost_item.category:
        candidates = candidates.filter(category=lost_item.category)

    scored_candidates: list[MatchCandidate] = []
    for found_item in candidates:
        found_detection = _detect_item_category_from_file(found_item.image)
        found_category = found_detection.get('category_value') or 'other'

        score = 0
        reasons: list[str] = []

        if lost_category != 'other' and found_category == lost_category:
            score += 45
            reasons.append(f'AI category match: {lost_category_label}')
        elif lost_item.category and found_item.category == lost_item.category:
            score += 35
            reasons.append(f'Stored category match: {found_item.get_category_display()}')

        if found_category == found_item.category:
            score += 10
            reasons.append('Found image detected consistently with stored category')

        text_bonus, text_reasons = _score_text_overlap(lost_item, found_item)
        score += text_bonus
        reasons.extend(text_reasons)

        lost_name = _normalize_text(lost_item.item_name)
        found_name = _normalize_text(found_item.item_name)
        if lost_name and found_name and (lost_name == found_name or lost_name in found_name or found_name in lost_name):
            score += 18
            reasons.append('Item name closely matches')

        if lost_item.location_lost and found_item.location_found and lost_item.location_lost == found_item.location_found:
            score += 6
            reasons.append('Location pattern matches')

        if found_item.claim_status == 'open':
            score += 4
            reasons.append('Item is still open')

        if found_item.image:
            score += 2

        scored_candidates.append(
            MatchCandidate(
                item=found_item,
                score=min(score, 100),
                reasons=reasons,
                detected_category=found_category,
                detection_message=found_detection.get('message', ''),
            )
        )

    scored_candidates.sort(key=lambda candidate: (candidate.score, candidate.item.updated_at, candidate.item.created_at), reverse=True)

    return {
        'lost_detection': lost_detection,
        'results': scored_candidates[:limit],
    }
