---
title: "What are .mtf, .mdf, .ldb and .log files (Trados TMs/termbases), and can I delete them?"
description: "A practical explanation of common Trados/MultiTerm sidecar files and when it’s safe to remove them."
pubDate: 2025-08-19
---

## MTF files

- **MTF** stands for **MultiTerm Termbase File**.
- These are temporary/supporting files created when working with SDL MultiTerm.
- They are **not** the termbase itself — the real termbase is stored in the `.sdltb` file.
- MTF files are often generated during export, import, or when a termbase is opened.

## MDF files

- MDF files are supporting database files linked to MultiTerm or (in some cases) older Trados translation memories.
- They can appear alongside other database components such as IDF, LDF or NDF.
- The actual termbase remains the `.sdltb` file, while translation memories are stored in `.sdltm` files.

## LDB files

- `.ldb` stands for **Lock Database file**.
- When an Access-based database (such as `.sdltb`) is opened, Windows creates an `.ldb` (or `.laccdb`) file to manage multi-user locking.
- It records which processes have the database open.
- It should disappear automatically once all applications using the termbase are closed.

## LOG files

- `.log` files are diagnostic/activity logs created by Trados Studio or MultiTerm during operations such as TM maintenance, termbase import/export, or error handling.
- They can be useful for troubleshooting and auditing operations.
- They do **not** contain active TM or termbase data.

## Can they be deleted?

- **MTF/MDF**: often safe to delete if you retain your primary `.sdltm` (TMs) and `.sdltb` (termbases). Trados/MultiTerm can typically regenerate them when needed.
- **LDB**: only delete if you’re sure the associated termbase is closed everywhere. If it remains after a crash/unexpected shutdown, it is usually safe to remove once no process is using the database.
- **LOG**: generally safe to delete when you no longer need them for troubleshooting or record-keeping.

As a precaution, back up any active project folders before removing files — especially in shared or multi-user environments.

## See also

- The Trados Tax: Why working with Trados Studio sucks — https://michaelbeijer.co.uk/trados_tax
- Update Main Translation Memories vs Update Project Translation Memory (Trados Studio) — https://michaelbeijer.co.uk/Update_Main_Translation_Memories_vs_Update_Project_Translation_Memory_(in_Trados_Studio)

---

Source: https://michaelbeijer.co.uk/Trados_MTF_and_MDF_files
