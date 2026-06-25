import logging

logger = logging.getLogger("event_engine")


# =========================================================
# EVENT STORE (SOURCE OF TRUTH)
# =========================================================
class EventStore:

    def __init__(self):

        self.events = []
        self.next_id = 1

    def add_event(self, event: dict):

        event = dict(event)

        if "id" not in event:

            event["id"] = self.next_id

            self.next_id += 1

        self.events.append(event)

        return event

    def get_history(self):

        return self.events


# =========================================================
# DATE RESOLVER
# =========================================================
def extract_event_date(df, index):

    logger.debug(
        f"[EVENT ENGINE] Resolving date "
        f"for candle index={index}"
    )

    if df is None:
        return "UNKNOWN"

    for candidate in (
        "Date",
        "date",
        "Datetime",
        "datetime",
        "Timestamp",
        "timestamp"
    ):

        if candidate in df.columns:

            try:

                logger.debug(
                    f"[EVENT ENGINE] Using column "
                    f"{candidate}"
                )

                return str(
                    df.iloc[index][candidate]
                )

            except Exception:
                pass

    try:

        idx = df.index[index]

        if not isinstance(
            idx,
            (int, float)
        ):
            return str(idx)

    except Exception:
        pass

    return "UNKNOWN"


# =========================================================
# RESOLVER
# =========================================================
def find_latest_unresolved_pattern(history):
    """
    Backward scan over EventStore history.
    NO detection.
    NO recomputation.
    """

    logger.info(
        "[EVENT ENGINE] Backward scanning event history"
    )

    if not history:
        return None

    for event in reversed(history):

        status = event.get("status")

        if status in (
            "FAILED",
            "EXPIRED",
            "CONFIRMED"
        ):
            continue

        if status == "PENDING":

            logger.info(
                f"[EVENT ENGINE] Found pending event "
                f"id={event.get('id')} "
                f"type={event.get('type')}"
            )

            return event

    return None


# =========================================================
# EVENT STATUS UPDATER
# =========================================================
def update_event_status(
    store,
    event_rules,
    df,
    f=float
):

    if not isinstance(
        store,
        EventStore
    ):
        raise TypeError(
            "update_event_status requires EventStore"
        )

    logger.info(
        f"[EVENT ENGINE] Updating lifecycle for "
        f"{len(store.events)} events"
    )

    for event in store.events:

        status = event.get("status")

        # -------------------------------------------------
        # DEAD EVENTS
        # -------------------------------------------------
        if status in (
            "FAILED",
            "EXPIRED",
        ):
            continue

        # -------------------------------------------------
        # VALIDATE INDEX
        # -------------------------------------------------
        try:

            event_index = int(
                event.get("index", 0)
            )

        except Exception:

            logger.warning(
                f"[EVENT ENGINE] Invalid index "
                f"for event {event.get('id')}"
            )

            continue

        start_index = event_index + 1

        # -------------------------------------------------
        # EVENT IS CURRENT CANDLE
        # -------------------------------------------------
        if start_index >= len(df):

            event.setdefault(
                "days_active",
                0
            )

            event.setdefault(
                "resolved_date",
                None
            )

            event.setdefault(
                "status_reason",
                "Still active"
            )

            logger.info(
                f"[EVENT ENGINE] Event "
                f"{event.get('id')} "
                f"is latest candle -> ACTIVE"
            )

            continue

        # -------------------------------------------------
        # VALIDATION LOOP
        # -------------------------------------------------
        for i in range(
            start_index,
            len(df)
        ):

            candle = df.iloc[i]

            try:

                close = f(
                    candle["Close"]
                )

                high = f(
                    candle["High"]
                )

                low = f(
                    candle["Low"]
                )

            except Exception as e:

                logger.warning(
                    f"[EVENT ENGINE] "
                    f"OHLC error at {i}: {e}"
                )

                continue

            event["days_active"] = (
                i - event_index
            )

            try:

                action = event_rules(
                    event=event,
                    candle=candle,
                    close=close,
                    high=high,
                    low=low
                )

            except Exception as e:

                logger.exception(
                    f"[EVENT ENGINE] "
                    f"rule error: {e}"
                )

                continue

            # =====================================================
            # CONFIRMATION
            # =====================================================
            if (
                action == "CONFIRM"
                and event["status"] == "PENDING"
            ):

                event["status"] = "CONFIRMED"

                event["resolved_date"] = (
                    extract_event_date(
                        df,
                        i
                    )
                )

                event["status_reason"] = (
                    "Confirmation condition met"
                )

                logger.info(
                    f"[EVENT ENGINE] Event "
                    f"{event.get('id')} "
                    f"CONFIRMED at "
                    f"{event['resolved_date']}"
                )

                break

            # =====================================================
            # FAILURE
            # =====================================================
            elif action == "FAIL":

                event["status"] = "FAILED"

                event["resolved_date"] = (
                    extract_event_date(
                        df,
                        i
                    )
                )

                event["status_reason"] = (
                    f"Invalidated at close {close}"
                )

                logger.info(
                    f"[EVENT ENGINE] Event "
                    f"{event.get('id')} "
                    f"FAILED at "
                    f"{event['resolved_date']}"
                )

                break

            # =====================================================
            # EXPIRATION
            # =====================================================
            elif action == "EXPIRE":

                event["status"] = "EXPIRED"

                event["resolved_date"] = (
                    extract_event_date(
                        df,
                        i
                    )
                )

                event["status_reason"] = (
                    "Expired without confirmation"
                )

                logger.info(
                    f"[EVENT ENGINE] Event "
                    f"{event.get('id')} "
                    f"EXPIRED at "
                    f"{event['resolved_date']}"
                )

                break

        logger.info(
            f"[EVENT ENGINE] Final status "
            f"id={event.get('id')} "
            f"status={event.get('status')}"
        )


# =========================================================
# STORE RECONCILIATION
# =========================================================
def reconcile_event_store(
    store,
    df,
    event_rules,
    f=float
):

    logger.info(
        "[EVENT ENGINE] Reconciling event store "
        "against latest price action"
    )

    update_event_status(
        store,
        event_rules,
        df,
        f
    )

    active = [

        e

        for e in store.events

        if e.get("status") == "PENDING"
    ]

    logger.info(
        f"[EVENT ENGINE] Active pending events "
        f"after reconciliation = "
        f"{len(active)}"
    )

    return store
