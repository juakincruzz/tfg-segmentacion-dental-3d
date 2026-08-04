# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status: no code yet

This is the TFG (Trabajo de Fin de Grado) of Joaquín Cruz Lorenzo, Grado en Ingeniería Informática, Universidad de Granada (ETSIIT). Tutor: Pablo Mesejo Santiago (DECSAI); mentor: Antonio David Villegas Yeguas.

The repository currently holds background research only. There is no source code, no build system, no test suite and no dependency manifest. Do not invent build/lint/test commands — none exist. If asked to run or test something, first check whether the code has been added since this file was written.

## Git

The repository is live at `github.com/juakincruzz/tfg-segmentacion-dental-3d` (public, MIT, default branch `main`).

The tutors have explicitly asked for Git to be used as a real version-control tool over the whole life of the project — successive commits spread over time, informative messages, branches where reasonable, and tests written as part of development rather than bolted on at the end. A tribunal member may inspect the history. So: commit as work happens, never batch unrelated changes, and **write commit messages in Spanish** to match the rest of the project.

## What is here

- `bibliografia/papers_url_tfg.txt` — the bibliography, one numbered entry per line in the form `[n] Title. DOI: <url>`. Source of truth for which papers belong to the project.
- `notas/` — reading notes, one per paper, written by the student. This is his own work and it is versioned.
- `papers_md/` — full text of papers converted to Markdown from their web versions (e.g. PMC scrapes). **Gitignored**: these are third-party copyrighted texts and are not redistributed from a public repository.
- `guias_tfg/` — Mesejo's memoria and presentation guides. **Gitignored**, same reason.
- `memoria/`, `src/`, `notebooks/`, `tests/` — empty scaffolding so far.
- `data/` — gitignored. Teeth3DS is CC BY-NC-ND 4.0 and must never be committed; test fixtures should be synthetic meshes generated in code.

Not every entry in `papers_url_tfg.txt` has a corresponding file in `papers_md/` — the collection is still being filled in. Keep the two in sync when adding a paper.

The converted Markdown is machine-generated and messy: headings alternate between `#`/`###` and setext underlines, in-text citations survive as `\[[12](#CIT0012)\]` anchors, MDPI scrapes carry ~260 lines of site boilerplate before the article starts, and figure images point at remote CDN URLs. Treat it as a corpus to read and quote, not as prose to be cleaned up unless asked.

## Research topic

The bibliography defines the intended direction: applying **3D intraoral scan data to forensic dental identification**, particularly disaster victim identification (DVI).

The three seed papers connect as a chain of motivation:

1. *Forensic odontology in DVI* establishes the problem — victim identification depends on matching antemortem to postmortem dental profiles, and the paper argues explicitly (see its "3D Surface scan data" sections) that 3D surface comparison is the future of the field and that the comparison process is a candidate for automation. It also flags the open questions: how much restorative or orthodontic treatment degrades a match, and the smallest jaw fragment that still supports identification.
2. *Clinical Application of Intraoral Scanners in Dentistry* covers the acquisition side — the scanners producing the antemortem 3D data that would make such matching possible.
3. *3DTeethSeg'22* is the computational side — a public challenge, dataset, and benchmark for segmenting and labeling individual teeth in 3D intraoral scans.

So the natural shape of any code added here is a 3D mesh / point-cloud pipeline: tooth segmentation and labeling, then registration or superimposition of two arches to score a match. Expect mesh formats (OBJ/PLY/STL) and the 3DTeethSeg'22 dataset conventions rather than a conventional application stack.

## Working language

Project artifacts and communication are in Spanish (UGR thesis); the source papers are in English. Match whichever the user is writing in.
