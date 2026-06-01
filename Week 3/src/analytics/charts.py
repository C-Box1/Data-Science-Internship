"""
analytics/charts.py
-------------------
Build Plotly chart JSON from query results for the website.
"""

from __future__ import annotations

import plotly.graph_objects as go


def bar_chart(title: str, labels: list[str], values: list[int], horizontal: bool = False) -> str:
    if horizontal:
        fig = go.Figure(go.Bar(x=values, y=labels, orientation="h"))
    else:
        fig = go.Figure(go.Bar(x=labels, y=values))

    fig.update_layout(
        title=title,
        template="plotly_white",
        margin=dict(l=40, r=20, t=50, b=80),
        xaxis_tickangle=-45 if not horizontal else 0,
    )
    return fig.to_json()


def pie_chart(
    title: str,
    labels: list[str],
    values: list[int],
    show_percentages: bool = True,
    max_items: int = None,
) -> str:
    """
    Create a pie chart with optional filtering to show only top N items.
    
    Args:
        title: Chart title
        labels: Category labels
        values: Corresponding values
        show_percentages: Whether to show percentages in labels
        max_items: Maximum number of items to show (rest grouped as "Other")
                  If None, show all items
    
    Returns:
        JSON string of the Plotly figure
    """
    if not labels or not values:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig.to_json()
    
    # Sort by values descending
    sorted_pairs = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
    
    # Apply max_items filtering
    if max_items and len(sorted_pairs) > max_items:
        top_pairs = sorted_pairs[:max_items]
        other_sum = sum(v for _, v in sorted_pairs[max_items:])
        if other_sum > 0:
            top_pairs.append(("Other", other_sum))
        sorted_pairs = top_pairs
    
    labels_sorted = [label for label, _ in sorted_pairs]
    values_sorted = [value for _, value in sorted_pairs]
    total = sum(values_sorted)
    
    # Create custom hover text with count and percentage
    hover_text = []
    for label, value in zip(labels_sorted, values_sorted):
        percentage = (value / total * 100) if total > 0 else 0
        hover_text.append(f"{label}<br>Count: {value}<br>Percentage: {percentage:.1f}%")
    
    # Create custom labels with count and percentage
    display_labels = []
    for label, value in zip(labels_sorted, values_sorted):
        percentage = (value / total * 100) if total > 0 else 0
        if show_percentages:
            display_labels.append(f"{label}<br>{value} ({percentage:.1f}%)")
        else:
            display_labels.append(f"{label}<br>{value}")
    
    fig = go.Figure(data=[go.Pie(
        labels=display_labels,
        values=values_sorted,
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover_text,
    )])
    
    fig.update_layout(
        title=title,
        template="plotly_white",
        margin=dict(l=40, r=20, t=50, b=40),
    )
    
    return fig.to_json()


def chart_from_rows(title: str, rows: list[dict], label_key: str, value_key: str) -> str:
    labels = [str(r[label_key]) for r in rows]
    values = [int(r[value_key]) for r in rows]
    horizontal = len(labels) > 8
    if horizontal:
        labels = labels[::-1]
        values = values[::-1]
    return bar_chart(title, labels, values, horizontal=horizontal)


def pie_chart_from_rows(
    title: str,
    rows: list[dict],
    label_key: str,
    value_key: str,
    max_items: int = None,
) -> str:
    """
    Create a pie chart from query rows with optional top-N filtering.
    
    Args:
        title: Chart title
        rows: List of dictionaries from database query
        label_key: Dictionary key for labels
        value_key: Dictionary key for values
        max_items: Maximum items to show (optional)
    
    Returns:
        JSON string of the Plotly figure
    """
    labels = [str(r[label_key]) for r in rows]
    values = [int(r[value_key]) for r in rows]
    return pie_chart(title, labels, values, max_items=max_items)
