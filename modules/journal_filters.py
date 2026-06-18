# journal_filters.py

def apply_journal_filters(
    tree,
    journal_rows,
    filter_search_var,
    filter_type_var,
    CSV_FIELDS,
    preview_text,
    filter_count_label
):

    tree.delete(*tree.get_children())

    search_text = filter_search_var.get().strip().lower()
    filter_type = filter_type_var.get()

    visible_count = 0

    for row in journal_rows:

        compare_value = str(row.get(filter_type, "")).lower()

        if search_text in compare_value:

            visible_values = []

            for field in CSV_FIELDS:

                value = row.get(field, "")

                if field in (
                    "trade_notes",
                    "analysis_notes",
                    "management_notes"
                ):
                    value = preview_text(value)

                visible_values.append(value)

            tree.insert("", "end", values=visible_values)

            visible_count += 1

    filter_count_label.config(
        text=f"{visible_count} Result(s)"
    )