---
type: entity
updated: 2026-09-22
status: current
sources: [5 DICOM slices from 1 test study, read with pydicom 2026-09-22]
---

# DICOM headers: what survives anonymisation

Rich acquisition metadata survives - echo time, scan options, series description,
laterality, scanner model - which means the true contrast of every series is
recoverable from the headers. **Measured on one study only**, so presence is certain
and prevalence is not.

## Sample

1 test study, 5 series, one slice each: Siemens MAGNETOM Avanto fit, 1.5 T,
uncompressed Explicit VR Little Endian, 12-bit, MONOCHROME2. Matrices 640-960
(one 3D series 640 x 1280), pixel spacing 0.16-0.25 mm, 3 mm slices with a 0.3 mm
gap, plus one 3D DESS water-excitation series at 0.6 mm. 0.8-1.8 MB per slice.

## 62 tags present

**Present** [Certain, in this sample]: `Laterality`, `Manufacturer`,
`ManufacturerModelName`, `MagneticFieldStrength`, `EchoTime`, `RepetitionTime`,
`InversionTime`, `FlipAngle`, `ScanningSequence`, `SequenceVariant`, `ScanOptions`,
`MRAcquisitionType`, `SeriesDescription`, `SliceThickness`, `SpacingBetweenSlices`,
`PixelSpacing`, `ImageOrientationPatient`, `ImagePositionPatient`, `SliceLocation`,
`InstanceNumber`, `AcquisitionMatrix`, `PixelBandwidth`, `EchoTrainLength`,
`ReceiveCoilName`, `PatientID`, `PatientSex`, `BodyPartExamined`,
`ContrastBolusAgent`, `WindowCenter`, `WindowWidth`, `RescaleSlope`,
`RescaleIntercept` and the pixel-format tags.

**Absent:** `PatientAge`, `StudyDate`, `InstitutionName`, `ProtocolName`,
`ImageLaterality`.

Older docs said "86 tags survive". Only 62 were seen here. [Unverified] whether 86
is the allowlist and some are simply unused by this scanner.

## The organisers' fluid flag misfiles T2 without fat-sat

| SeriesDescription | TE | TR | ScanOptions | CSV fluid / fs | physics |
|---|---|---|---|---|---|
| `t2_tse_sag_d` | 91 | 5000 | PER | **0 / 0** | **T2, fluid-sensitive, no fat-sat** |
| `pd_tse_fs_cor_d` | 42 | 3400 | SP, FS, PER | 1 / 1 | intermediate-weighted fat-sat |
| `pd_tse_sag_d` | 9 | 3000 | SP, PER | 0 / 0 | PD, structural |
| `pd_tse_tra_d` | 46 | 3000 | PER | 0 / 0 | intermediate-weighted, no fat-sat |
| `t2_de3d_we_tra_Patella` | 7 | 18 | PER | 1 / 1 | 3D DESS, water-excitation - fluid-bright |

[Certain] The T2 TSE row is the misfiling predicted in `wiki/archive/FINDINGS.md`
item 14: a textbook fluid-sensitive series labelled structural. Every public
solution slots it as structural.

Note two things the headers teach that a naive rule gets wrong: water-excitation
(`_we_`) is a fat-suppression technique that does **not** set `FS` in
`ScanOptions`, and DESS is fluid-bright despite a 7 ms echo time. Type sequences from
`SeriesDescription` + `ScanOptions` + `EchoTime` together - which is what
`src/sequence_typing.py` does.

## Consequences

- **Laterality** can come straight from the `Laterality` tag, if it is present
  across the set.
- **The true fluid axis is recoverable**, so the 2x2 slot grid in `src/sampling.py`
  (`full=True`) has something to consume.
- **`PatientID`** may allow patient-grouped CV folds.

All three need the census: `notebooks/header_census.ipynb`, CPU only.

Related: [[dataset]], [[slice-selection]], [[preprocessing-contract]]
