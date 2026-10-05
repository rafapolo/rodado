# Dengue in Brazil: from notification to hospital to death

Between 2014 and 2024 Brazil's surveillance system recorded **16.7 million probable cases
of dengue** and **12,788 deaths** from it. Public hospitals admitted 567,723 patients with a
dengue diagnosis and were paid R$ 231.7 million for it. These numbers come from three
national systems that were never designed to talk to each other: the notifiable-diseases
register (SINAN), the hospital billing system of the public health service (SIH/SUS) and
the mortality register (SIM).

This piece follows a dengue case through all three, the way a real-world-data team would
before using them for a study: what each system sees, where they agree, where they don't,
and what questions they can carry. The last part, *fit for purpose*, matters most.

![Bar charts: probable dengue cases, SUS hospital admissions and deaths by year, Brazil 2014–2024](/analises/img/dengue-funnel-2014-2024.png)

## 2024 was off the scale

Dengue in Brazil comes in waves: 2015–16, 2019, 2022–23. Each of these produced between
1.4 and 1.7 million probable cases. **2024 produced 6.4 million**, 3.8 times the previous
record. It hit every step of the funnel at once: 158,910 SUS admissions, 6,270 deaths.

Deaths grew faster than cases: 6.2 times the 2015 count, against 3.8 times for cases. Case
fatality went from 5.9 to 9.7 deaths per 10,000 probable cases. Part of that is the age of
those infected (see below), and part is what happened inside hospitals.

**The hospital picture has been shifting for a decade.** In 2014 there was one SUS
admission for every 16 probable cases. In 2024 there was one for every 40. Over the same
period, in-hospital mortality among dengue admissions rose from 0.45% to 1.58%. Fewer cases
reach a hospital bed, and those who do are sicker. This is consistent with clinical
management that treats non-severe cases with hydration in primary care and reserves beds
for warning signs. It is also consistent with more admissions going to private hospitals,
which SIH does not see. The
data alone can't separate the two explanations, and saying so is part of the job.

A dengue admission is short and cheap: 3.4 days on average and R$ 509 paid per admission in
2024, up from R$ 327 in 2014 at current prices.

![Weekly probable dengue cases by week of symptom onset, 2014–2025](/analises/img/dengue-weekly-2014-2025.png)

## A seasonal disease with a moving peak

Week by week, the pattern is regular. Cases peak between epidemiological weeks 8 and 19,
from late February to mid-May, after the summer rains. In 2024 the peak came in week 12,
with **424,000 new cases in seven days**, four times the tallest week of any earlier year.
2025 came in second, with 191,000 at its peak.

For any study design this is the first constraint: the exposure window is narrow, and
annual totals hide it. A cohort or a vaccine-effectiveness analysis has to be built by
epidemiological week, not by calendar year.

![Incidence and case fatality by state of residence, 2014–2024](/analises/img/dengue-states-2014-2024.png)

## Where it strikes is not where it kills

Pooled over 2014–2024, the epidemics concentrate in the Centre-South. Goiás notified 1,850
probable cases per 100,000 people a year, the Federal District 1,580 and Minas Gerais
1,550. The North and Northeast notify far less.

Case fatality ranks differently. Sergipe (15.1 deaths per 10,000 cases), the Federal
District (12.9), Rio Grande do Sul (11.9) and Maranhão (11.5) lose more patients per case
than São Paulo (8.2). The national figure is 7.7. A low-incidence state with high fatality
can mean two things: real gaps in care, or under-notification of mild cases, which inflates
the ratio. Telling them apart requires the hospital and mortality data, and that is where
the integration starts.

**Espírito Santo is the warning in this chart.** It looks like a low-incidence state. It
isn't: between 2021 and 2024 the state notified dengue through its own system, and it
nearly disappears from the national file. The section on data quality comes back to it.

![Deaths from dengue recorded by surveillance, death certificates and SUS hospitals, 2014–2024](/analises/img/dengue-deaths-by-source-2014-2024.png)

## Three systems, three death counts

The same deaths are counted three times, and the counts differ.

- **Surveillance (SINAN)** closes a notified case with outcome "death from the disease"
  after an investigation. 5,422 deaths between 2014 and 2022.
- **Death certificates (SIM)** record dengue as the underlying cause of death. 5,925 in
  the same years, 9% more. Certificate microdata are available up to 2022.
- **SUS hospitals (SIH)** record a death during an admission whose principal diagnosis was
  dengue. 2,755 in the same period, about half.

None of these is wrong. Each counts a different event. SIH sees only deaths inside public
hospitals, during an admission coded as dengue. SIM sees deaths certified as dengue,
including those that were never notified. SINAN sees deaths among notified cases. **No
patient identifier links them**: the public files carry no common ID, so the three can only
be compared in aggregate, by place and time. Linking at patient level, which claims and EHR
databases such as Optum, Flatiron or CPRD allow, is not possible here without restricted
access.

The two systems that should agree best, SINAN and SIM, stay within about 15% of each other
from 2014 to 2019 and drift apart afterwards. In 2021 certificates named dengue 404 times
against 277 deaths closed by surveillance; in 2022, 1,244 against 1,051.

![Case fatality by age group, with and without diabetes and hypertension, 2024](/analises/img/dengue-age-comorbidity-2024.png)

## Age sets the risk, comorbidities multiply it

SINAN is record-level data, so it allows a question the other two can't answer: who dies?

In 2024 case fatality rose from 0.21 per 1,000 among children under 15 to **15.3 per 1,000
among people over 80**, more than seventyfold. Within each age group, a recorded
comorbidity still adds risk. Among people aged 60–79, those with diabetes recorded on the
notification form died 2.9 times as often as those without. The pattern for hypertension is
similar.

A caveat a pharma reader should apply: the comorbidity fields are filled more carefully
when a case is severe, so part of the gap may come from how the form is filled in, not from
biology. The field only became usable in 2017. In 2014 and 2015 it was blank for almost every
record.

![Dengue incidence and case fatality by quintile of municipal GDP per capita and sanitation, nationwide and within each state](/analises/img/dengue-sdoh-2014-2024.png)

## The social gradient that isn't there

Real-world evidence increasingly joins clinical data to social determinants of health:
income, sanitation, education. Brazil has these by municipality, for every municipality,
which most commercial RWD sources lack. So the obvious test is to group
municipalities into fifths of the population by GDP per capita and by sewage treatment, and
compare.

Nationwide, the result looks clear and goes the "wrong" way: **richer municipalities notify
more dengue and lose more patients per case** (5.6 deaths per 10,000 cases in the poorest
fifth, 8.7 in the richest). Rank municipalities within their own state instead, and the
fatality gradient mostly flattens (7.0 to 7.9). The national slope reflects which states
had epidemics, not poverty. Sanitation shows no fatality gradient at all. That is
biologically expected: *Aedes aegypti* breeds in clean standing water, not in sewage.

The finding is mostly negative, and it is the useful kind. A naive pooled analysis would
report a strong and wrong social gradient. Three things would have to be controlled before
any social-determinants claim: geography (state), age structure (richer places are older)
and notification capacity (richer places detect and report more mild cases).

![Completeness of key surveillance fields by year, and Espírito Santo's reporting gap](/analises/img/dengue-data-quality-2014-2025.png)

## Fit for purpose: what this data can and cannot do

In the vocabulary of FDA and EMA guidance on real-world evidence, the question is not "is
the data good?" but "is it good enough for this question?". Measured on the files
themselves:

**What it can carry**

- Burden and trends at national, state and municipal level, by epidemiological week,
  with near-complete coverage of notified cases since 2014.
- Record-level risk factors within SINAN: age, sex, comorbidities (since 2017), warning
  signs and severity.
- Health-care use and cost of public admissions (SIH): length of stay, ICU use, amount
  paid per admission.
- Ecological linkage to social and environmental data by municipality.

**What it cannot carry, or only with care**

- **Patient-level linkage across systems.** There is no shared identifier in the public
  files. Every cross-system comparison here is ecological.
- **Private care.** SIH covers SUS admissions only. About one in four Brazilians has
  private health insurance, and their admissions are invisible to it.
- **Laboratory confirmation.** Only 34–37% of probable cases in 2024–2025 were confirmed
  by a laboratory test; the rest are clinical-epidemiological.
- **Hospitalisation and outcome on the notification form.** The hospitalisation field is
  blank or "unknown" for 26–30% of recent cases, and the outcome for about 20%. Counting
  hospitalisations from SINAN alone undercounts them.
- **Complete geography.** Espírito Santo notified 64,735 probable cases in 2019 and 575 in
  2024, while SUS hospitals admitted 2,669 of its residents for dengue that year. A
  state-level model that does not check for this treats a reporting gap as an absence of
  disease.
- **Comparable series over time.** Cases are classified under WHO 2009 categories since
  2014, with different codes before that. From 2022 the public file no longer includes
  discarded notifications, so "all notifications" means different things before and after.
  The comorbidity fields start in practice in 2017.
- **Cause-of-death quality.** 6.1% of all deaths in 2022 had an ill-defined cause (ICD-10
  R00–R99), from 1.2% in Espírito Santo to 15.7% in Acre. Dengue deaths hidden there are
  not counted anywhere.

**Privacy.** The hospital and surveillance files include date of birth, sex, municipality
and, in SIH, the patient's postcode. Everything published here is aggregated, and cells
with fewer than 10 deaths are suppressed.

## Method

- **Sources.** Ministry of Health / DATASUS: SINAN dengue (notifications 2014–2025), SIH/SUS
  reduced admission records (admissions 2014–2024), SIM (deaths 2014–2022). IBGE municipal
  population (estimates up to 2021, Census 2022 from 2022) and GDP 2021. National Water
  Agency (ANA), *Atlas Esgotos*, for sewage treatment.
- **Probable case.** Every notification except those classified as discarded. Confirmed =
  dengue, dengue with warning signs or severe dengue. Deaths = outcome "death from the
  disease".
- **Admissions.** Principal diagnosis ICD-10 A90 (dengue) or A91 (dengue haemorrhagic
  fever), normal admission records only (no continuation records), counted by date of
  admission, so admissions billed in the following year are included. A97, the newer dengue
  code, does not appear in SIH or SIM in this period.
- **Deaths on certificates.** Underlying cause A90–A91.
- **Geography.** Patient's municipality of residence in all three systems. SIH stores the
  6-digit municipality code and SINAN and SIM the 7-digit one; they were matched through
  the IBGE municipality directory.
- **Rates.** Crude, not age-standardised. State incidence uses the 2014–2024 mean
  population. Quintiles are weighted by population, so each fifth holds about the same
  number of people. Espírito Santo is excluded from the social-determinants comparison.
- **Checks.** National totals match the sum by state of residence plus the cases with no
  municipality: 6,434,137 probable cases in 2024 both ways. The 2024 death count (6,270)
  matches the order of magnitude published by the Ministry of Health for that year.

*Data run on 5 October 2026.*
