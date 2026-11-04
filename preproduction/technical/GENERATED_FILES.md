# Generated files and reproducibility

- Run `python tools/export_localization_csv.py` to rebuild `exports/localization_de.csv` in UTF-8 with BOM for spreadsheet compatibility; **not automatically a valid Unreal DataTable**.
- Run `python tools/export_quest_graph.py` to rebuild `exports/quest_graph.dot` (Graphviz optional).
- `preview/story_flow_preview.html` embeds a snapshot of `data/v3/` created at package build time. After modifying canonical JSON, regenerate/review the preview; do not treat it as an authoritative editor.
- Python tests in `tests/` and v3 JSON are authoritative for offline state consistency only. UE integration and rendering need separate tests.
