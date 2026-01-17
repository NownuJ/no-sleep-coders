from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


def rank_pages_by_importance(all_pages):
    """
    Rank pages by composite score:
    - TF-IDF importance
    - Formula presence
    - Definition presence
    - Heading count
    
    Returns: sorted list of pages with importance scores
    """
    if not all_pages:
        return []
    
    # Extract texts
    texts = [p.get("full_text", "") for p in all_pages]
    
    # Remove empty pages
    valid_indices = [i for i, t in enumerate(texts) if t.strip()]
    if not valid_indices:
        return all_pages
    
    valid_texts = [texts[i] for i in valid_indices]
    
    # TF-IDF scoring
    try:
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2),
            max_df=0.85,
            min_df=1
        )
        
        tfidf_matrix = vectorizer.fit_transform(valid_texts)
        # Sum TF-IDF scores per document
        tfidf_scores = np.array(tfidf_matrix.sum(axis=1)).flatten()
        
        # Normalize to 0-1
        if tfidf_scores.max() > 0:
            tfidf_scores = tfidf_scores / tfidf_scores.max()
    except Exception as e:
        print(f"TF-IDF failed: {e}, using fallback scoring")
        tfidf_scores = np.ones(len(valid_texts))
    
    # Calculate composite scores for all pages
    ranked_pages = []
    tfidf_idx = 0
    
    for i, page in enumerate(all_pages):
        # Get TF-IDF score if page was valid
        if i in valid_indices:
            tfidf_score = tfidf_scores[tfidf_idx]
            tfidf_idx += 1
        else:
            tfidf_score = 0
        
        # Composite score
        score = (
            0.40 * tfidf_score +
            0.30 * (3.0 if page.get("has_formula") else 0) +
            0.20 * (2.0 if page.get("has_definition") else 0) +
            0.10 * min(len(page.get("headings", [])), 3)  # Cap at 3 headings
        )
        
        page["importance_score"] = float(score)
        page["tfidf_score"] = float(tfidf_score)
        ranked_pages.append(page)
    
    # Sort by score descending
    ranked_pages.sort(key=lambda x: x["importance_score"], reverse=True)
    
    return ranked_pages


def select_top_chunks(ranked_pages, max_pages=80):
    """
    Select top N pages for API processing
    Prioritize: formulas > definitions > high TF-IDF
    """
    if len(ranked_pages) <= max_pages:
        return ranked_pages
    
    # Always include formula pages
    formula_pages = [p for p in ranked_pages if p.get("has_formula")]
    definition_pages = [p for p in ranked_pages if p.get("has_definition")]
    
    # Combine and dedupe
    selected = []
    seen_indices = set()
    
    # Add formula pages first
    for p in formula_pages:
        idx = p.get("page")
        if idx not in seen_indices:
            selected.append(p)
            seen_indices.add(idx)
    
    # Add definition pages
    for p in definition_pages:
        idx = p.get("page")
        if idx not in seen_indices and len(selected) < max_pages:
            selected.append(p)
            seen_indices.add(idx)
    
    # Fill remaining with highest ranked
    for p in ranked_pages:
        idx = p.get("page")
        if idx not in seen_indices and len(selected) < max_pages:
            selected.append(p)
            seen_indices.add(idx)
        
        if len(selected) >= max_pages:
            break
    
    return selected