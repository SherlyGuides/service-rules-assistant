"""Documents the library still needs: the data behind the public page site-home/needed/ and its PDF.

Edit SECTIONS when a document arrives or a new gap is found, then run build_site.py (it rebuilds both).
"""
import html
import os
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FONT = os.path.join(ROOT, "site-home", "fonts", "Geist-Variable.woff2")
E = html.escape

# (section title, who-note, rows) ; row = (document, reference, who has it, priority H/M)
SECTIONS = [
    ("Delhi Government school teachers (Directorate of Education)",
     "Almost all of these are on the DoE staff login (edudel.nic.in, MIS / Del-E). One teacher or Head of School "
     "with a login can download most of them in about half an hour.",
     [
         ("Online transfer circulars for teaching staff, 2020, 2021, 2022, 2025 and 2026", "File DE.2(8)(5)/E-II/On-line Tr.", "Any DoE teacher or HoS login; E-II Branch", "H"),
         ("Order of July 2024 holding transfers of teachers with 10+ years in one school in abeyance, and the committee formed after it", "July 2024", "E-II Branch; Secretary (Education)", "H"),
         ("Surplus teacher (post fixation) transfer circular; mutual transfer circulars", "No. 898 dt 08.11.2021 (link broken)", "E-II / E-III; Post Fixation Cell", "M"),
         ("Casual leave rules and procedure for DoE teachers", "", "HoS login; GOC / Admin Branch", "H"),
         ("Child care leave orders", "F.4(35)/2005/GOC/Edu/6189-6200 dt 29.05.2013; F.4(35)/2005/GOC/Ed./17487-17498 dt 03.12.2013", "GOC Branch", "H"),
         ("Earned leave for vacation staff (March 2021) and compensatory leave orders", "17.11.2020; 27.11.2022", "Admin / School Branch", "H"),
         ("Compensatory or earned leave for teachers doing BLO duty on holidays", "about 24.09.2026", "School Branch; any HoS", "H"),
         ("MACP-II consolidated guidelines for teachers, and the earlier circular", "DE-3(4)/ACP Cell/GCC/2016/8242-82410 dt 31.08.2020; 19.12.2019", "ACP Cell / E-III", "H"),
         ("APAR benchmark upgradation (Good to Very Good) for 2016-17 and 2017-18", "31.08.2020; 02.12.2020", "E-III / ACP Cell", "M"),
         ("Online APAR instructions for teachers (2021-22 onwards); delinking of health report", "Jan 2021 onwards", "E-III; Services Dept (e-SPARROW)", "M"),
         ("Pay fixation on promotion / MACP option circular", "2021", "Pay & Pension Branch", "M"),
         ("DPC eligibility and schedule circulars (TGT to PGT, PGT to VP, VP to Principal); seniority principles", "", "E-II / E-III; Secretariat Branch", "M"),
         ("Re-employment of teachers, VPs and Principals discontinued", "10.09.2020", "Secretariat Branch", "M"),
         ("Online pension papers (MIS pension module); HoS responsibility for pension, gratuity and leave encashment", "Feb 2023; Jan 2022", "Pension & Pay Fixation Branch", "M"),
         ("Aadhaar biometric attendance resumed; any salary-linkage order", "Aug 2022", "IT Branch / Admin", "M"),
         ("Study leave / NOC for higher studies; NOC for foreign visits", "2024", "Admin / E-Branches", "M"),
         ("Teacher duty hours and school timing orders; BLO and election deployment policy for teachers", "", "School Branch; CEO Delhi", "H"),
         ("Vigilance and suspension general circulars", "", "Vigilance Branch", "M"),
         ("Mentor Teacher Programme and Teacher Development Coordinator scheme orders; SCERT in-service training hours policy", "2016-17", "SCERT Delhi; School Branch", "M"),
         ("Allotment of Delhi Government pool housing to school staff", "Letter dt 27.12.1991 and current rules", "GAD / Directorate of Estates", "M"),
     ]),
    ("Guest teachers (Delhi)", "Guest teacher associations usually keep these.",
     [
         ("Casual leave and paternity leave orders for guest teachers", "", "E-V Branch (guest teacher cell); guest teacher associations", "H"),
         ("Remuneration revisions after 2018", "2019 onwards", "E-V / Planning Branch", "H"),
         ("Maternity benefit order for guest teachers", "24.07.2018", "E-V Branch", "M"),
         ("Engagement terms for the 2020-21 reserve panel (base notice)", "", "E-V Branch", "M"),
         ("Text of the Regularisation of Services of Guest Teachers Bill, 2017", "Delhi Assembly, Oct 2017", "Delhi Legislative Assembly Secretariat", "M"),
     ]),
    ("Private recognised and aided schools (Delhi)", "",
     [
         ("All current Aided School Branch circulars: grant-in-aid, post sanctions, pension / GPF / NPS-OPS, 7th CPC and MACP for aided staff, applicability of CCS rules", "", "Any aided school's Head or accounts clerk; DoE Aided School Branch", "H"),
         ("6th CPC implementation and fee increase in unaided schools", "F.DE/15(56)/Act/2009/778 dt 11.02.2009", "Private school teacher associations; DoE Act Branch", "H"),
         ("Gratuity circular for unaided schools", "DE/15(29)/Act/Orders/2008/5144-5161 dt 25.06.2008", "DoE Private School Branch", "M"),
         ("Orders cited in the 7th CPC order of 17.10.2017", "19.02.2016; 16.04.2016; 03.07.2017", "DoE Private School Branch", "M"),
         ("Delhi School Tribunal: procedure, limitation, court fee, current address and Presiding Officer notification", "", "An advocate who practises before the Tribunal; Tribunal registry", "H"),
         ("Registration of untrained private-school teachers for NIOS D.El.Ed.", "DE.15(280)/PSB/2017/18559-18567 dt 15.09.2017", "DoE Private School Branch", "M"),
         ("Old aided-school circulars 2008-09 (surplus staff, reservation, ACR committee)", "files broken on edudel", "DoE Aided School Branch", "M"),
     ]),
    ("NDMC and Delhi Cantonment Board schools", "",
     [
         ("NDMC teachers' transfer / posting policy", "", "NDMC Education Department; NDMC teachers", "H"),
         ("Final notified NDMC recruitment rules after 2022 (TGT, Primary, VP, Special Educator)", "only drafts are online", "NDMC Education Establishment", "M"),
         ("NDMC teacher circulars on leave, MACP and APAR", "", "NDMC Personnel / Education", "M"),
         ("Delhi Cantonment Board school teachers' service rules, recruitment rules and transfer policy", "website was down", "Cantonment Board school staff; CEO office", "M"),
     ]),
    ("Election and census duty", "",
     [
         ("Census 2027 honorarium (financial norms) circular", "ORGI Circular No. 7 dt 24.12.2025", "Any census charge officer / DCO office; teachers on census duty", "H"),
         ("Census 2027 circulars on appointment, duties, training and leave of census staff; enumerator and supervisor manuals", "", "Census trainers; DCO / ORGI", "H"),
         ("ECI BLO Guidelines (teachers to be drafted minimally, never from single-teacher schools)", "No. 23/BLO/2022-ERS dt 04.10.2022", "Any ERO / BLO supervisor; CEO Delhi", "H"),
         ("CEO Delhi orders on exempting teachers from polling or BLO duty, and how to apply", "", "CEO Delhi; DEO offices", "H"),
         ("CEO Delhi: 'Regarding Election Duty of BLOs' and 'TA to employees on election duty'", "17.01.2015; 12.12.2019", "CEO Delhi", "M"),
         ("Latest orders in the Delhi High Court BLO case", "W.P.(C) 10174/2026, hearing 06.10.2026", "Advocates in the case; Delhi HC website", "H"),
     ]),
    ("Delhi Police", "A defence assistant or the DE cell will have these.",
     [
         ("Delhi Police (Punishment and Appeal) (Amendment) Rules, 2020: Delhi Gazette notification", "2020", "DE cell, legal cell, defence assistants", "H"),
         ("Standing Order A-20 (departmental enquiries) and current DE circulars", "", "DE cell / establishment branch", "H"),
         ("Circulars on suspension, defence assistants and bar period", "2005", "Establishment branch", "M"),
     ]),
    ("KVS and NVS teachers", "",
     [
         ("NVS Recruitment Rules (2023 revision) and Supplementary General Rules", "", "NVS teachers, principals, regional office", "H"),
         ("NVS Transfer Guidelines 2024", "15.11.2023", "NVS teachers", "H"),
         ("NVS circulars on house-master allowance, 10% special allowance and weekly off", "", "NVS teachers", "M"),
         ("KVS Education Code (full, current) and KVS Accounts Code (final notified version)", "", "KVS administrative staff; principals", "H"),
         ("Any KVS transfer policy amendment after 2023", "", "KVS teachers, principals", "M"),
     ]),
    ("Central Government rule books still missing",
     "These are public. We will keep trying to collect them; send a copy if you have one.",
     [
         ("Fundamental Rules and Supplementary Rules (FR/SR), current official edition", "DoPT / DoE", "Any establishment section", "H"),
         ("CCS (Medical Attendance) Rules, 1944", "MoHFW", "Any establishment section", "M"),
         ("Central Government Employees Group Insurance Scheme, 1980 (scheme rules)", "DoE", "Any accounts section", "M"),
         ("General Pool Residential Accommodation (GPRA) Rules, 2017 (full text)", "Directorate of Estates", "Estate offices", "M"),
         ("House Building Advance Rules, 2017", "MoHUA", "Any accounts section", "M"),
         ("Central Administrative Tribunal (Procedure) Rules, 1987 and CAT Practice Rules", "CAT", "Service-law advocates", "M"),
         ("Income-tax Act, 2025 (text)", "CBDT", "", "M"),
         ("CAT Principal Bench orders on teachers and other Central staff, by topic", "", "Service-law advocates", "M"),
     ]),
    ("Other departments (later phases)",
     "Large public manuals we will collect; employees of these departments can send their own office orders.",
     [
         ("Railways: Establishment Manual Vols I and II, Establishment Code, Discipline and Appeal Rules 1968, Conduct Rules 1966, Pension Rules 1993, Revised Pay Rules 2016, pass rules", "", "Railway employees", "M"),
         ("Department of Posts: Postal Manual Vols III and IV; GDS (Conduct and Engagement) Rules, 2020", "", "Postal employees", "M"),
         ("Central Armed Police Forces: CRPF, BSF, CISF, ITBP, SSB and Assam Rifles Acts and Rules", "", "CAPF personnel", "M"),
         ("Defence civilians: service instructions; Ordnance and MES establishment orders", "", "Defence civilian employees", "M"),
     ]),
    ("Blank forms (for automatic form filling)",
     "Needed to build the form-filling feature users have asked for. A clean blank copy of each is enough.",
     [
         ("Leave application form (Form 1, CCS (Leave) Rules) and DoE Delhi leave format", "", "Any office", "H"),
         ("LTC advance and LTC claim forms", "", "Any office", "H"),
         ("TA claim form (tour and transfer)", "", "Any office", "M"),
         ("GPF advance / withdrawal forms", "", "Any accounts section", "H"),
         ("CGHS card application; NPS / UPS option forms", "", "CGHS wellness centre; DDO", "M"),
         ("Delhi DoE formats: MACP application, NOC, study leave, re-joining after leave", "", "Any DoE school office", "M"),
     ]),
]

DOWNLOADS = [
    ("Representation of the People Act, 1951 (current)", "https://www.indiacode.nic.in/bitstream/123456789/2096/1/Rp1951.pdf"),
    ("Representation of the People Act, 1950 (current)", "https://upload.indiacode.nic.in/showfile?actid=AC_CEN_3_20_00016_195043_1517807321506&filename=03_representation_of_the_people_act%2C_1950.pdf&type=actfile"),
    ("Conduct of Elections Rules, 1961 (current)", "https://upload.indiacode.nic.in/showfile?actid=AC_CEN_3_81_00001_195143_1517807327542&filename=2.conduct_of_election_rules%2C_1961.doc.pdf&type=rule"),
]

QUESTIONS = [
    "Do teachers (vacation staff) get half pay leave, given Rule 29(1) of the CCS (Leave) Rules as substituted in 2018?",
    "Is KVS still crediting earned leave at 2/5 of vacation days worked (memo of 31.08.2022)?",
    "Who actually decides Delhi Police appeals against DCP orders today: Additional CP or Joint CP?",
    "Has the special air LTC scheme (to 25.09.2026) been extended?",
    "How many days of casual leave do Delhi DoE teachers and guest teachers actually get, and under which order?",
]


def table(rows):
    out = ['<table><thead><tr><th class="c-doc">Document</th><th class="c-ref">Reference</th>'
           '<th class="c-who">Who is likely to have it</th><th class="c-pri">Priority</th></tr></thead><tbody>']
    for doc, ref, who, pri in rows:
        p = '<span class="pri hi">High</span>' if pri == "H" else '<span class="pri">Medium</span>'
        out.append(f"<tr><td>{E(doc)}</td><td class='ref'>{E(ref)}</td><td>{E(who)}</td><td>{p}</td></tr>")
    out.append("</tbody></table>")
    return "".join(out)


def build_pdf(out: str) -> tuple[int, int]:
    """Print the list to a PDF at `out` with headless Chrome; returns (items, high priority)."""
    total = sum(len(r) for _, _, r in SECTIONS)
    high = sum(1 for _, _, r in SECTIONS for x in r if x[3] == "H")
    body = []
    for i, (title, note, rows) in enumerate(SECTIONS, 1):
        body.append(f"<section><h2><span class='num'>{i}</span>{E(title)}</h2>"
                    + (f"<p class='note'>{E(note)}</p>" if note else "") + table(rows) + "</section>")
    dl = "".join(f"<li><b>{E(t)}</b><br><span class='url'>{E(u)}</span></li>" for t, u in DOWNLOADS)
    qs = "".join(f"<li>{E(q)}</li>" for q in QUESTIONS)

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Documents Needed for the Library</title>
    <style>
    @font-face {{ font-family: Geist; src: url("file://{FONT}") format("woff2"); font-weight: 100 900; }}
    @page {{ size: A4; margin: 16mm 14mm 16mm 14mm;
      @bottom-right {{ content: counter(page) " / " counter(pages); font: 8pt Geist, sans-serif; color: #888; }} }}
    * {{ box-sizing: border-box; }}
    body {{ font: 9.2pt/1.42 Geist, -apple-system, Helvetica, sans-serif; color: #18181b; margin: 0; }}
    .cover {{ border-bottom: 2px solid #18181b; padding-bottom: 12px; margin-bottom: 14px; }}
    .kicker {{ font-size: 8pt; letter-spacing: .08em; text-transform: uppercase; color: #8a6d2f; font-weight: 600; margin: 0 0 6px; }}
    h1 {{ font-size: 22pt; line-height: 1.1; letter-spacing: -.02em; margin: 0 0 6px; font-weight: 650; }}
    .sub {{ color: #52525b; margin: 0; font-size: 10pt; max-width: 150mm; }}
    .stats {{ display: flex; gap: 0; margin: 14px 0 4px; border: 1px solid #e4e4e7; border-radius: 6px; }}
    .stats div {{ flex: 1; padding: 8px 12px; }} .stats div + div {{ border-left: 1px solid #e4e4e7; }}
    .stats b {{ display: block; font-size: 15pt; font-weight: 650; letter-spacing: -.02em; }}
    .stats span {{ color: #71717a; font-size: 8pt; }}
    .how {{ background: #faf7f0; border: 1px solid #eadfc8; border-radius: 6px; padding: 10px 12px; margin: 12px 0 4px; }}
    .how h3 {{ margin: 0 0 4px; font-size: 10pt; }} .how ol {{ margin: 0; padding-left: 16px; }} .how li {{ margin: 2px 0; }}
    section {{ margin-top: 14px; }} section:last-of-type {{ break-inside: avoid; }}
    h2 {{ font-size: 12pt; margin: 0 0 4px; font-weight: 650; letter-spacing: -.01em; break-after: avoid; display: flex; align-items: baseline; gap: 8px; }}
    .num {{ display: inline-block; min-width: 18px; height: 18px; line-height: 18px; text-align: center; border-radius: 9px;
      background: #18181b; color: #fff; font-size: 8pt; font-weight: 600; }}
    .note {{ margin: 0 0 6px; color: #52525b; break-after: avoid; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    thead {{ display: table-header-group; }}
    th {{ text-align: left; font-size: 7.6pt; text-transform: uppercase; letter-spacing: .05em; color: #71717a; font-weight: 600;
      border-bottom: 1px solid #d4d4d8; padding: 4px 6px; }}
    td {{ border-bottom: 1px solid #ececef; padding: 5px 6px; vertical-align: top; }}
    tr {{ break-inside: avoid; }}
    .c-doc {{ width: 44%; }} .c-ref {{ width: 22%; }} .c-who {{ width: 23%; }} .c-pri {{ width: 11%; }}
    td.ref {{ color: #52525b; font-size: 8.4pt; word-break: break-word; }}
    .pri {{ font-size: 7.6pt; font-weight: 600; padding: 1px 6px; border-radius: 8px; background: #f4f4f5; color: #52525b; white-space: nowrap; }}
    .pri.hi {{ background: #18181b; color: #fff; }}
    ul.dl {{ padding-left: 16px; margin: 4px 0 0; }} ul.dl li {{ margin: 0 0 6px; break-inside: avoid; }}
    .url {{ font-size: 7.6pt; color: #52525b; word-break: break-all; }}
    ol.q {{ padding-left: 16px; margin: 4px 0 0; }} ol.q li {{ margin: 0 0 4px; }}
    .foot {{ margin-top: 18px; padding-top: 8px; border-top: 1px solid #e4e4e7; color: #71717a; font-size: 8pt; }}
    </style></head><body>
    <div class="cover">
      <p class="kicker">Service Rules Assistant · Library request</p>
      <h1>Documents Needed for the Library</h1>
      <p class="sub">Official documents the assistant cannot yet cite, mostly because they sit behind a staff login or were never put online. If you have any of these, please share a copy. A photo of each page is enough.</p>
      <div class="stats">
        <div><b>2,580</b><span>documents already in the library</span></div>
        <div><b>{total}</b><span>documents still needed</span></div>
        <div><b>{high}</b><span>marked high priority</span></div>
      </div>
      <div class="how"><h3>How to send a document</h3><ol>
        <li>Open the Service Rules Assistant: sherlyguides.github.io/vidhi-sahayak (or see the live list at sherlyguides.github.io/service-rules-assistant/needed/)</li>
        <li>Attach the PDF, Word file or photos and type <b>for the library</b>. Each file is checked before it is added.</li>
        <li>Or send it to the person who shared this list with you.</li>
      </ol></div>
    </div>
    {''.join(body)}
    <section><h2><span class="num">{len(SECTIONS) + 1}</span>Quick downloads by hand</h2>
    <p class="note">The official site blocks automated downloads. Opening each link in a browser and saving the PDF is enough.</p>
    <ul class="dl">{dl}</ul></section>
    <section><h2><span class="num">{len(SECTIONS) + 2}</span>Questions only practitioners can settle</h2>
    <p class="note">The written rules are unclear or out of date on these. An answer from someone who handles them at work helps.</p>
    <ol class="q">{qs}</ol>
    <p class="foot">List as of 5 October 2026. Priority is based on what users ask most. Only official documents are added; nothing personal from a shared file is published.</p></section>
    </body></html>"""

    src = os.path.join(tempfile.mkdtemp(), "needed.html")
    open(src, "w").write(page)
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                    f"--print-to-pdf={out}", "file://" + src], check=True, capture_output=True, timeout=120)
    return total, high


def counts() -> tuple[int, int]:
    return sum(len(r) for _, _, r in SECTIONS), sum(1 for _, _, r in SECTIONS for x in r if x[3] == "H")
