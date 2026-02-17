import pandas as pd
from safefeat.spec import WindowAgg, RecencyBlock, FeatureSpec
from safefeat.audit import AuditReport, TableAudit

def build_features(spine, tables, spec, *, entity_col="entity_id", cutoff_col="cutoff_time",
                   event_time_cols=None, allowed_lag="0s", return_report=False):
    """Build leakage-safe features from event tables.

    Parameters
    ----------
    spine : pandas.DataFrame
        DataFrame containing entity identifiers and cutoff times.
    tables : dict[str, pandas.DataFrame]
        Mapping of table name to event DataFrame.
    spec : FeatureSpec or list[WindowAgg]
        Feature specification describing windows and aggregations.
    entity_col : str, default="entity_id"
        Name of entity identifier column.
    cutoff_col : str, default="cutoff_time"
        Name of cutoff timestamp column.
    event_time_cols : dict[str, str]
        Mapping of table name to event timestamp column.
    allowed_lag : str, default="0s"
        Allowed tolerance for future timestamps (pandas timedelta string).
    return_report : bool, default=False
        If True, return a tuple ``(features_df, AuditReport)`` with audit
        information about dropped/kept event pairs.

    Returns
    -------
    pandas.DataFrame or (pandas.DataFrame, AuditReport)
        Feature matrix aligned to the spine. If ``return_report`` is True a
        second return value contains the audit report.
    """
    
    if event_time_cols is None:
        raise ValueError("event_time_cols must be provided, e.g. {'events': 'event_time'}")

    # validate spine
    if entity_col not in spine.columns or cutoff_col not in spine.columns:
        raise ValueError(f"Required columns {entity_col} and/or {cutoff_col} not found in spine DataFrame")
    
    out = spine.copy()
    out[cutoff_col] = pd.to_datetime(out[cutoff_col], errors="raise")
    spine_subset = out[[entity_col, cutoff_col]]
    
    report = AuditReport() if return_report else None

    if isinstance(spec, list):
        spec = FeatureSpec(blocks=spec)
        
    for block in spec.blocks:
        if isinstance(block, WindowAgg): 
            events_df = tables[block.table] # get the events table specified in the block
            event_time_col = event_time_cols[block.table] # get the event time column for this table
            
            # Collect audit on first window; reuse for subsequent windows or report
            audit_data_for_table = None

            for w in block.windows: # for each window specified in the block
                # get events in the window using the helper function
                result = _events_in_window(
                    spine=spine_subset,
                    events=events_df,
                    time_window=w,
                    allowed_lag=allowed_lag,
                    entity_col=entity_col,
                    cutoff_col=cutoff_col,
                    event_time_col=event_time_col,
                    collect_audit=return_report,
                )
                
                if return_report:
                    in_window, audit_data = result
                    # Only capture audit from first window (it's the same for all windows of the same table)
                    if audit_data_for_table is None:
                        audit_data_for_table = audit_data
                else:
                    in_window = result

                # process each metric in block.metrics
                for dim, aggs in block.metrics.items():
                    if dim != "*" and dim not in in_window.columns:
                        raise ValueError(f"Column '{dim}' not found in table '{block.table}'")
            
                    if dim == "*":
                        # wildcard: count
                        if "count" in aggs:
                            counts = (
                                in_window.groupby([entity_col, cutoff_col], sort=False)
                                .size()
                                .reset_index(name="count")
                            )
                            feature_name = f"{block.table}__n_events__{w.lower()}"
                            merged = spine_subset.merge(counts, on=[entity_col, cutoff_col], how="left")
                            out[feature_name] = merged["count"].fillna(0).astype(int).values
                    else:
                        gb = in_window.groupby([entity_col, cutoff_col], sort=False)

                        # named column aggregations
                        if "sum" in aggs:
                            sum_agg = (
                                gb[dim]
                                .sum()
                                .reset_index(name="sum_val")
                            )
                            feature_name = f"{block.table}__{dim}__sum__{w.lower()}"
                            merged = spine_subset.merge(sum_agg, on=[entity_col, cutoff_col], how="left")
                            out[feature_name] = merged["sum_val"].fillna(0).values

                        if "mean" in aggs:
                            mean_agg = (
                                gb[dim]
                                .mean()
                                .reset_index(name="mean_val")
                            )
                            feature_name = f"{block.table}__{dim}__mean__{w.lower()}"
                            merged = spine_subset.merge(mean_agg, on=[entity_col, cutoff_col], how="left")
                            out[feature_name] = merged["mean_val"].fillna(0).values
                        if "nunique" in aggs:
                            nunique_agg = (
                                gb[dim]
                                .nunique()
                                .reset_index(name="nunique_val")
                            )
                            feature_name = f"{block.table}__{dim}__nunique__{w.lower()}"
                            merged = spine_subset.merge(nunique_agg, on=[entity_col, cutoff_col], how="left")
                            out[feature_name] = merged["nunique_val"].fillna(0).astype(int).values
            
            # Add audit data for this table if collecting reports
            if return_report and audit_data_for_table is not None:
                table_audit = TableAudit(
                    table=block.table,
                    total_joined_pairs=audit_data_for_table["total_joined_pairs"],
                    kept_pairs=audit_data_for_table["kept_pairs"],
                    dropped_future_pairs=audit_data_for_table["dropped_future_pairs"],
                    max_future_delta=audit_data_for_table["max_future_delta"],
                )
                report.add_table(table_audit)

        elif isinstance(block, RecencyBlock): # compute recency feature
            events_df = tables[block.table]
            event_time_col = event_time_cols[block.table]
            
            # Filter events if a filter is specified
            filtered_events = events_df.copy()
            if block.filter_col is not None: 
                filtered_events = filtered_events[filtered_events[block.filter_col] == block.filter_value] 
            
            # Compute time since last event for each entity-cutoff pair
            recency_features = _compute_recency(
                spine=spine_subset,
                events=filtered_events,
                entity_col=entity_col,
                cutoff_col=cutoff_col,
                event_time_col=event_time_col,
                allowed_lag=allowed_lag,
            )
            
            # Add recency feature column
            feature_name = f"{block.table}__recency"
            if block.filter_col is not None:
                feature_name += f"__{block.filter_col}_{block.filter_value}"
            
            merged = spine_subset.merge(recency_features, on=[entity_col, cutoff_col], how="left")
            out[feature_name] = merged["recency_days"].values

        else:
            raise ValueError(f"Unknown block type: {type(block)}")

    if return_report:
        return out, report
    return out


def filter_events_point_in_time(spine, events, *,  allowed_lag="0s", entity_col="entity_id", cutoff_col="cutoff_time", event_time_col="event_time", time_window= "30D", collect_audit=False):
    """Join events to the spine and enforce point-in-time filtering.

    This function merges ``spine`` and ``events`` on ``entity_col`` to create
    entity-cutoff × event pairs, then removes any pairs where the event
    occurs after the cutoff (subject to ``allowed_lag``).

    Parameters
    ----------
    spine, events : pandas.DataFrame
        Input DataFrames. ``spine`` must contain ``entity_col`` and
        ``cutoff_col``; ``events`` must contain ``entity_col`` and
        ``event_time_col``.
    allowed_lag : str
        Pandas-compatible timedelta string giving a grace period for late
        events (e.g. ``"24h"``).
    collect_audit : bool
        If True the function returns ``(filtered_df, audit_dict)`` where
        ``audit_dict`` contains counts of joined/kept/dropped pairs and the
        maximum future delta.

    Returns
    -------
    pandas.DataFrame or (pandas.DataFrame, dict)
        Filtered DataFrame (and optional audit dictionary).
    """

    if entity_col not in spine.columns or cutoff_col not in spine.columns:
        raise ValueError(f"Required columns {entity_col} and/or {cutoff_col} not found in spine DataFrame")

    if entity_col not in events.columns or event_time_col not in events.columns:
        raise ValueError(f"Required columns {entity_col} and/or {event_time_col} not found in events DataFrame")

    # parse timestamp columns
    spine = spine.copy()
    events = events.copy()
    spine[cutoff_col] = pd.to_datetime(spine[cutoff_col], errors="raise")
    events[event_time_col] = pd.to_datetime(events[event_time_col], errors="raise")

    merged_df = spine.merge(events, on=entity_col, how="inner")
    total_joined_pairs = len(merged_df) # total number of event-spine pairs before filtering out future events
    
    #Apply the "no future" rule
    allowed_lag_td = pd.to_timedelta(allowed_lag)
    future_mask = merged_df[event_time_col] > (merged_df[cutoff_col] + allowed_lag_td)
    dropped_future = merged_df[future_mask].copy()
    dropped_future_pairs = len(dropped_future)
    
    merged_df = merged_df[~future_mask]
    kept_pairs = len(merged_df)
    
    audit_dict = None
    if collect_audit:
        max_future_delta = None
        if dropped_future_pairs > 0:
            deltas = dropped_future[event_time_col] - (dropped_future[cutoff_col] + allowed_lag_td)
            max_future_delta = deltas.max() # the largest amount of time by which dropped events were in the future
        
        audit_dict = {
            "total_joined_pairs": total_joined_pairs, # total number of event-spine pairs before filtering
            "kept_pairs": kept_pairs, # number of pairs kept after filtering out future events
            "dropped_future_pairs": dropped_future_pairs, # number of pairs dropped due to being in the future
            "max_future_delta": max_future_delta, # the largest amount of time by which dropped events were in the future (None if no events dropped)
        }
        return merged_df, audit_dict
    
    return merged_df


def _events_in_window(
    spine,
    events,
    *,
    time_window,
    allowed_lag="0s",
    entity_col="entity_id",
    cutoff_col="cutoff_time",
    event_time_col="event_time",
    collect_audit=False,
):
    """Return events joined to entity-cutoff pairs restricted to a window.

    This helper first calls :func:`filter_events_point_in_time` to apply the
    "no future" rule and (optionally) collect audit info, then further
    restricts the joined pairs to those whose ``event_time`` falls within the
    lookback defined by ``time_window`` before the cutoff.

    Parameters
    ----------
    time_window : str
        Pandas-compatible timedelta string (e.g. ``"30D"``) defining how far
        back from the cutoff to include events.
    collect_audit : bool
        If True return a tuple ``(in_window_df, audit_dict)``.

    Returns
    -------
    pandas.DataFrame or (pandas.DataFrame, dict)
        Filtered events in the window and optional audit dictionary.
    """

    result = filter_events_point_in_time(
        spine=spine,
        events=events,
        entity_col=entity_col,
        cutoff_col=cutoff_col,
        event_time_col=event_time_col,
        allowed_lag=allowed_lag,
        collect_audit=collect_audit,
    )

    if collect_audit:
        filtered, audit_dict = result
    else:
        filtered = result
        audit_dict = None

    window_start = filtered[cutoff_col] - pd.to_timedelta(time_window)
    mask = (filtered[event_time_col] > window_start) & (filtered[event_time_col] <= filtered[cutoff_col])
    in_window = filtered.loc[mask]

    if collect_audit:
        return in_window, audit_dict
    return in_window



def count_events_in_window(spine, events, *, allowed_lag="0s", entity_col="entity_id", cutoff_col="cutoff_time", event_time_col="event_time", time_window= "30D"):
    """Count events per entity-cutoff within the lookback window.

    This is a convenience wrapper used by older tests and examples. It
    returns a DataFrame with an ``event_count_{time_window}`` column aligned
    to the provided ``spine``.
    """
    spine2 = spine.copy()
    spine2[cutoff_col] = pd.to_datetime(spine2[cutoff_col], errors="raise")

    in_window = _events_in_window(
        spine2,
        events,
        time_window=time_window,
        allowed_lag=allowed_lag,
        entity_col=entity_col,
        cutoff_col=cutoff_col,
        event_time_col=event_time_col,
    )

    counts = (
        in_window.groupby([entity_col, cutoff_col], sort=False)
        .size()
        .reset_index(name=f"event_count_{time_window}")
    )

    out = spine2.merge(counts, on=[entity_col, cutoff_col], how="left")
    out[f"event_count_{time_window}"] = out[f"event_count_{time_window}"].fillna(0).astype(int)
    return out


def _compute_recency(
    spine,
    events,
    *,
    entity_col="entity_id",
    cutoff_col="cutoff_time",
    event_time_col="event_time",
    allowed_lag="0s",
):
    """Compute time since last event for each entity-cutoff pair.
    
    Returns a DataFrame with columns [entity_col, cutoff_col, 'recency_days']
    where recency_days is the number of days since the last event (negative if no events)
    """
    spine2 = spine.copy()
    spine2[cutoff_col] = pd.to_datetime(spine2[cutoff_col], errors="raise")
    
    filtered = filter_events_point_in_time(
        spine=spine2,
        events=events,
        entity_col=entity_col,
        cutoff_col=cutoff_col,
        event_time_col=event_time_col,
        allowed_lag=allowed_lag,
    )
    
    # For each entity-cutoff pair, find the most recent event
    last_events = (
        filtered.groupby([entity_col, cutoff_col])
        .agg({event_time_col: "max"})
        .reset_index()
        .rename(columns={event_time_col: "last_event_time"})
    )
    
    # Compute recency as days between cutoff and last event
    last_events["recency_days"] = (last_events[cutoff_col] - last_events["last_event_time"]).dt.days
    
    return last_events[[entity_col, cutoff_col, "recency_days"]]




