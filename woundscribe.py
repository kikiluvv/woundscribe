import typer
from rich.console import Console
from core import ocr, parser, splitter, db
from core.db import load_db, save_db
from pathlib import Path

app = typer.Typer()
console = Console()

@app.command()
def process(
    pdf_path: str = typer.Argument(..., help="Path to the monolithic wound note PDF."),
    output: str = typer.Option("./output", "--output", "-o", help="Output folder for processed PDFs."),
    auto_review: bool = typer.Option(True, "--auto-review/--no-auto-review", help="Automatically launch review if unknown patients found."),
):
    console.rule("[bold green]WoundScribe – PDF Processor[/]")
    console.print(f"📄 Processing: {pdf_path}")

    # step 1 – OCR
    page_texts = ocr.extract_texts(pdf_path)
    console.print(f"🧠 OCR complete for {len(page_texts)} pages")

    # step 2 – parse document boundaries
    docs = parser.detect_docs(page_texts)
    console.print(f"📑 Detected {len(docs)} patient sections")

    # step 3 – load DB
    patient_db = db.load_db()

    # step 4 – split + name
    results, fuzzy_hits = splitter.split_pdf(pdf_path, docs, output, patient_db)

    # step 5 – save updated DB
    db.save_db(patient_db)

    # step 6 – summary
    console.rule("[bold cyan]📊 Summary[/]")

    from rich.table import Table
    table = Table(title="Processing Results", show_lines=True)
    table.add_column("Clinic", style="cyan")
    table.add_column("Patients", style="bold white")
    table.add_column("Files Created", style="dim")

    clinic_summary = {}
    total_files = 0
    unknown_patients = []

    for entry in results:
        clinic = entry.get("clinic", "UnknownClinic")
        name = entry.get("name")
        clinic_summary.setdefault(clinic, {"patients": [], "files": 0})
        clinic_summary[clinic]["patients"].append(name)
        clinic_summary[clinic]["files"] += 1
        total_files += 1
        if clinic == "UnknownClinic":
            unknown_patients.append(name)

    for clinic, data in clinic_summary.items():
        table.add_row(
            clinic,
            ", ".join(data["patients"]),
            str(data["files"])
        )

    console.print(table)
    console.print(f"📦 Total PDFs generated: [bold]{total_files}[/]")

    if unknown_patients:
        console.print(f"[yellow]⚠️ Unknown patients:[/]\n - " + "\n - ".join(unknown_patients))

        # 🔗 chain into review if requested
        if auto_review:
            console.print("\n[blue]🌀 Launching interactive review now...[/]")
            review()

    if fuzzy_hits:
        console.print("\n[blue]🔍 Possible duplicate matches detected (review suggested):[/]")
        for clean_name, probable_match, score in fuzzy_hits:
            console.print(f"  - [bold]{clean_name}[/] ≈ [cyan]{probable_match}[/] ({score:.0f}%)")

        # optional: chain fuzzy review too
        if auto_review:
            console.print("\n[yellow]⚠️ Launching fuzzy duplicate review...[/]")
            review_fuzzy_matches(fuzzy_hits, patient_db)

    console.rule("[bold green]✅ Finished[/]")



@app.command()
def assign(
    name: str = typer.Argument(..., help="Full name of the patient."),
    clinic: str = typer.Option(..., "--clinic", "-c", help="Clinic name to assign.")
):
    """
    Assign or update a patient’s clinic.
    """
    import datetime
    patient_db = db.load_db()

    patient_db[name] = {
        "clinic": clinic,
        "last_updated": datetime.date.today().isoformat()
    }

    db.save_db(patient_db)
    console.print(f"✅ Assigned [bold]{name}[/] to clinic [cyan]{clinic}[/]")

@app.command()
def list():
    """
    List all known patients and their assigned clinics.
    """
    from rich.table import Table

    patient_db = db.load_db()

    if not patient_db:
        console.print("[yellow]⚠️ No patients found in database yet.[/]")
        return

    table = Table(title="📋 Known Patients", show_lines=True)
    table.add_column("Name", style="bold white")
    table.add_column("Clinic", style="cyan")
    table.add_column("Last Updated", style="dim")

    for name, data in sorted(patient_db.items()):
        clinic = data.get("clinic", "Unknown")
        last_updated = data.get("last_updated", "—")
        table.add_row(name, clinic, last_updated)

    console.print(table)

@app.command()
def remove(
    name: str = typer.Argument(..., help="Full name of the patient to remove.")
):
    """
    Remove a patient from the database.
    """
    patient_db = db.load_db()

    if name not in patient_db:
        console.print(f"[red]❌ {name} not found in database.[/]")
        raise typer.Exit(code=1)

    del patient_db[name]
    db.save_db(patient_db)
    console.print(f"🗑️ Removed [bold]{name}[/] from database.")

@app.command()
def rename(
    old_name: str = typer.Argument(..., help="Current name in the database."),
    new_name: str = typer.Argument(..., help="New name to assign.")
):
    """
    Rename a patient in the database.
    """
    import datetime
    patient_db = db.load_db()

    if old_name not in patient_db:
        console.print(f"[red]❌ {old_name} not found in database.[/]")
        raise typer.Exit(code=1)

    data = patient_db.pop(old_name)
    data["last_updated"] = datetime.date.today().isoformat()
    patient_db[new_name] = data

    db.save_db(patient_db)
    console.print(f"✏️ Renamed [bold]{old_name}[/] → [green]{new_name}[/]")

def review_fuzzy_matches(fuzzy_hits, patient_db):
    """
    Interactive fuzzy duplicate reviewer that cleans up duplicates
    in the patient_db without hardcoding any names.
    """
    import datetime

    console.rule("[bold yellow]🔍 Reviewing Possible Duplicates[/]")
    for clean_name, probable_match, score in fuzzy_hits:
        console.print(f"🤔 Possible duplicate detected:")
        console.print(f"  [bold cyan]{clean_name}[/] ≈ [bold green]{probable_match}[/] ({score:.1f}%)")
        action = console.input("Is this a duplicate? (y/n) [default: n]: ").strip().lower()

        if action == "y":
            # Merge + cleanup logic
            if probable_match in patient_db:
                source_data = patient_db.pop(clean_name, None)
                target_data = patient_db[probable_match]

                # If both have data, merge carefully
                if source_data:
                    merged = {**target_data, **source_data}
                    merged["last_updated"] = datetime.date.today().isoformat()
                    patient_db[probable_match] = merged

                console.print(
                    f"✅ Merged and cleaned up [bold cyan]{clean_name}[/] → [bold green]{probable_match}[/]."
                )
            else:
                # if for some reason the target doesn’t exist yet
                patient_db[probable_match] = patient_db.pop(clean_name)
                console.print(
                    f"⚠️ Target name not found; renamed [bold cyan]{clean_name}[/] → [green]{probable_match}[/]."
                )
        else:
            console.print(f"⏭️ Skipped [bold cyan]{clean_name}[/].")

    # Save once at the end to persist all changes
    save_db(patient_db)
    console.rule("[bold green]🎉 Duplicate Review Complete![/]")


@app.command()
def review():
    """
    Review patients assigned to 'UnknownClinic' and manually assign them.
    """
    import datetime

    patient_db = load_db()
    unknown_patients = [name for name, info in patient_db.items() if info["clinic"] == "UnknownClinic"]

    if unknown_patients:
        console.rule("[bold yellow]🔍 Reviewing Unknown Patients[/]")
        for name in unknown_patients:
            console.print(f"🤔 Unknown patient: [bold cyan]{name}[/]")
            clinic = console.input("Assign a clinic (or press Enter to skip): ").strip()
            if not clinic:
                console.print("[dim]⏭️ Skipped.[/]")
                continue
            patient_db[name]["clinic"] = clinic
            patient_db[name]["last_updated"] = datetime.date.today().isoformat()
            console.print(f"✅ Assigned [bold]{name}[/] → [cyan]{clinic}[/]")

        save_db(patient_db)
        console.rule("[bold green]🎉 Unknown Patient Review Complete![/]")

    # Add fuzzy match review
    fuzzy_hits = []  # Replace with actual fuzzy_hits from split_pdf
    if fuzzy_hits:
        review_fuzzy_matches(fuzzy_hits, patient_db)
    else:
        console.print("[bold green]No duplicates detected![/]")

if __name__ == "__main__":
    app()
