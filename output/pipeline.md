# Pipeline de la fábrica

```mermaid
flowchart LR
  s0["architect<br/>164 s"]:::ok
  s1["architect<br/>117 s"]:::ok
  s2["qa-unit<br/>349 s"]:::ok
  s3["verify unit<br/>35 s"]:::fail
  s4["observability<br/>358 s"]:::ok
  s5["security<br/>418 s"]:::ok
  s6["qa-unit<br/>29 s"]:::ok
  s7["verify unit<br/>19 s"]:::ok
  s8["verify contract<br/>17 s"]:::ok
  s9["verify qa<br/>20 s"]:::ok
  s10["verify e2e<br/>17 s"]:::ok
  s11["verify evaluate<br/>9 s"]:::ok
  s12["qa-style<br/>88 s"]:::ok
  s13["architect<br/>39 s"]:::ok
  s14["observability<br/>17 s"]:::ok
  s15["verify qa<br/>20 s"]:::ok
  s0 --> s1
  s0 --> s2
  s1 --> s3
  s2 --> s3
  s3 --> s4
  s4 --> s5
  s4 --> s6
  s5 --> s7
  s6 --> s7
  s7 --> s8
  s8 --> s9
  s9 --> s10
  s10 --> s11
  s11 --> s12
  s12 --> s13
  s12 --> s14
  s13 --> s15
  s14 --> s15
  classDef ok fill:#d4f4dd,stroke:#1e7b3a
  classDef fail fill:#fde2e2,stroke:#a12a2a
```

| # | Paso | Resultado | Segundos |
| --- | --- | --- | --- |
| 1 | architect | pasó | 164 |
| 2 | architect | pasó | 117 |
| 3 | qa-unit | pasó | 349 |
| 4 | verify unit | falló | 35 |
| 5 | observability | pasó | 358 |
| 6 | security | pasó | 418 |
| 7 | qa-unit | pasó | 29 |
| 8 | verify unit | pasó | 19 |
| 9 | verify contract | pasó | 17 |
| 10 | verify qa | pasó | 20 |
| 11 | verify e2e | pasó | 17 |
| 12 | verify evaluate | pasó | 9 |
| 13 | qa-style | pasó | 88 |
| 14 | architect | pasó | 39 |
| 15 | observability | pasó | 17 |
| 16 | verify qa | pasó | 20 |
