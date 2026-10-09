"""Student lens: how directly each URL delivers a 'product' (knowledge, skill, thinking, opportunity, wellbeing)
to the learner, and a plain-language note on what each URL is for.

Used by build_report.py:  assign(rows, urls)  adds the columns
  'Reaches learner', 'Eventual product for learner', 'What it is / used for'.
"""
import re
from urllib.parse import urlsplit

ROLE = {
    "D": "1 · Direct to learner",
    "G": "2 · Shelf / gateway to learner products",
    "T": "3 · Via teacher / parent / volunteer",
    "S": "4 · Via system design (curriculum, assessment, research)",
    "P": "5 · Publicity & event records",
    "O": "6 · Organisation upkeep (admin, jobs, tenders, legal)",
    "X": "7 · General external links",
}
ROLE_EXPLAIN = {
    "D": "The learner can open it and learn / practise / benefit from it right now: textbooks-like material, primers, "
         "worksheets, story books, videos, audio lessons, question papers, career & wellbeing help. The product itself.",
    "G": "A page that lists products (a shelf or signboard). One click away from the product. Useful, but only as good "
         "as what it leads to.",
    "T": "Made for the adult who teaches the learner – teacher handbooks, training courses, assessment packages, "
         "guides for parents/volunteers. Reaches the student only if the adult uses it well.",
    "S": "Shapes the whole system – curriculum frameworks, policies, syllabus design, national learning surveys, "
         "monitoring tools, research. Reaches the student years later through new textbooks, teachers and schools.",
    "P": "Shows that something happened – photo galleries, news, press clippings, event pages, social-media accounts. "
         "No learning product inside.",
    "O": "Keeps the organisation running – staff lists, committees, minutes, jobs, tenders, accounts, RTI/legal "
         "disclosures, guest house, contact pages. Nothing for the learner.",
    "X": "Standard links to other government or general websites (usually in the page footer).",
}
PRODUCTS = ["Career, money & opportunity", "Wellbeing & safety", "Skill", "Thinking & creativity", "Knowledge"]
NONE = "— (nothing for learner)"
MIXED = "Mixed (shelf of many products)"

PRODUCT_RX = [
    ("Career, money & opportunity", r"ntse|talent.?search|scholar|career|tamanna|aptitude|vocation|psscive|pgdvet|\bjobs?\b|employ|placement|sathee|skill.?india|finishing.?school|व्यावसायिक|करियर|छात्रवृत्ति"),
    ("Wellbeing & safety", r"health|wellness|well-being|manodarpan|mental|yoga|safety|komal|abuse|cwsn|disab|accessib|sign.?language|divyang|gender|adolescen|raksha|disaster|counsel|inclusive|braille|स्वास्थ्य|योग|सुरक्षा|दिव्यांग|परामर्श"),
    ("Skill", r"\bkits?\b|kit.?manual|lab.?manual|laborator|practical|\bart\b|arts|kala|music|dance|theatre|craft|\btoys?\b|kaushal|skill|sports|physical.?education|experiment|कला|किट|प्रयोगशाला"),
    ("Thinking & creativity", r"question|test.?paper|sample|exemplar|olympiad|quiz|competition|exhibit|rbvp|prayaas|innovation|project.?book|creative|assessment.?item|puzzle|magazine|sapno|firkee|प्रश्न|प्रतियोगिता|पत्रिका"),
]
PRODUCT_RX = [(n, re.compile(r, re.I)) for n, r in PRODUCT_RX]

# ---------------------------------------------------------------------------------------------------------------
# Hand-written notes for named pages (path on ncert.nic.in, lower-case) -> (role, product or None=auto, note)
# ---------------------------------------------------------------------------------------------------------------
PAGES = {
    "/": ("G", MIXED, "NCERT home page – entry point that links to everything on the site."),
    "/index.php": ("G", MIXED, "NCERT home page – entry point that links to everything on the site."),
    "/about-us.php": ("O", None, "About NCERT – its history, mandate and structure."),
    "/feedback.php": ("O", None, "Contact / feedback page of NCERT."),
    "/management.php": ("O", None, "NCERT's governing bodies, Memorandum of Association, rules and committees."),
    "/memorandum.php": ("O", None, "Memorandum of Association (NCERT's founding legal document)."),
    "/appendix-i.php": ("O", None, "Appendix to NCERT's rules / Memorandum of Association."),
    "/appendix-ii.php": ("O", None, "Appendix to NCERT's rules / Memorandum of Association."),
    "/miscellaneous.php": ("O", None, "Miscellaneous office notices."),
    "/archive-miscellaneous.php": ("O", None, "Archive of old miscellaneous notices."),
    "/nellore_about_us.php": ("T", None, "About RIE Nellore – one of NCERT's Regional Institutes of Education (colleges that train teachers)."),
    "/regional-institutes-education.php": ("T", None, "NCERT's Regional Institutes of Education (RIEs) – colleges that train school teachers (B.Ed, M.Ed etc.)."),
    "/national-institute-education.php": ("O", None, "About the National Institute of Education – NCERT's Delhi campus that houses its academic departments."),
    "/programme-advisory-committee.php": ("O", None, "Programme Advisory Committee – approves NCERT's yearly work plan; meeting minutes."),
    "/senior-functionaries.php": ("O", None, "List of NCERT's top officers (Director, Joint Director, Secretary…)."),
    "/telephone-directory.php": ("O", None, "Telephone directory of NCERT staff."),
    "/screen-reader.php": ("O", None, "Help page for blind users who browse with screen-reader software."),
    "/term-of-use.html": ("O", None, "Website terms of use."),
    "/disclo_un_rti.php": ("O", None, "Information NCERT must publish under the Right to Information (RTI) Act – for citizens seeking information."),
    "/public-information-officers.php": ("O", None, "Officers who answer RTI applications."),
    "/notices.php": ("O", None, "Office notices – mostly for staff, job applicants and partner institutions."),
    "/notices-archive.php": ("O", None, "Archive of old office notices."),
    "/other-announcements.php": ("O", None, "Other announcements (programmes, admissions, events) – mixed audience."),
    "/archive-academic.php": ("O", None, "Archive of old academic job announcements."),
    "/archive-non-academic.php": ("O", None, "Archive of old non-academic job announcements."),
    "/archive-project-staff.php": ("O", None, "Archive of old contract/project staff job announcements."),
    "/archive-results.php": ("O", None, "Archive of recruitment results."),
    "/archive-dcgc.php": ("T", None, "Archive of the Diploma Course in Guidance & Counselling (a course for teachers)."),
    "/vacancies.php": ("O", None, "Job vacancies at NCERT."),
    "/tenders.php": ("O", None, "Tenders – NCERT buying goods/services (printing, equipment, works) from vendors."),
    "/tenders-archive.php": ("O", None, "Archive of old tenders."),
    "/annual-accounts.php": ("O", None, "NCERT's audited annual accounts (finance)."),
    "/annual-report.php": ("O", None, "NCERT's annual reports – a record of what the organisation did each year."),
    "/result-framework-doc.php": ("O", None, "Results Framework Document – NCERT's yearly targets reported to the Ministry."),
    "/dc_searchdata.php": ("O", None, "Site search results page."),
    "/pss-vocational-education.php": ("O", None, "About PSSCIVE, Bhopal – NCERT's institute for vocational (job-skill) education."),
    "/books-indent-form.php": ("G", None, "Bulk order form to buy NCERT books – the physical delivery channel of books to schools and sellers."),
    "/information-customers.php": ("G", None, "Information for book buyers – prices, how and where to buy NCERT books."),
    "/childrens-book.php": ("G", None, "Shelf of NCERT's children's story and reading books (beyond textbooks)."),
    "/ebooks.php": ("G", None, "Online textbooks page."),
    "/textbook.php": ("G", None, "Main textbook selector: pick class → subject → book to read or download any NCERT textbook (PDF)."),
    "/textbooks.php": ("G", None, "Textbooks landing page."),
    "/state-uts-ebook.php": ("G", None, "Textbooks of different States/UTs as e-books (ePub)."),
    "/vocational-education.php": ("G", None, "Vocational textbooks – job-skill subjects for Classes 9–12."),
    "/vocational.php": ("G", None, "Vocational textbook selector – job-skill subjects for Classes 9–12."),
    "/psscive.php": ("G", None, "Vocational textbooks written by PSSCIVE (NCERT's vocational institute, Bhopal)."),
    "/exemplar-problems.php": ("G", "Thinking & creativity", "Exemplar Problems – extra, higher-level practice questions for students of Classes 6–12."),
    "/list-publication.php": ("G", MIXED, "Complete list of NCERT publications with prices."),
    "/other-publications.php": ("G", MIXED, "Other (non-textbook) NCERT publications."),
    "/non-print-materials.php": ("G", MIXED, "NCERT's audio, video and digital (non-print) materials."),
    "/media-programmes.php": ("G", None, "Educational audio/video programmes made by NCERT (TV, radio, online)."),
    "/journals-and-periodicals.php": ("G", MIXED, "NCERT journals and periodicals – research journals for educators plus magazines for children."),
    "/ict-initiatives.php": ("G", MIXED, "List of NCERT's digital learning platforms & apps (DIKSHA, ePathshala, PM eVidya, NROER…)."),
    "/eresources.php": ("G", MIXED, "e-Resources – links to digital learning platforms."),
    "/school-kits-and-lab-manual.php": ("G", "Skill", "School science/maths kits and the manuals that explain how to use them."),
    "/accessibility.php": ("G", "Wellbeing & safety", "Accessibility resources – e-content and help for children with disabilities."),
    "/science-laboratory-manual.php": ("D", "Skill", "Science laboratory manuals and demonstration videos for school practicals."),
    "/bridge_programme.php": ("D", None, "Bridge Programme for Grades 1, 3, 5, 6 & 8 – short subject booklets that help students move to the new NCF-based textbooks."),
    "/udaanshikshaki.php": ("D", None, "Udaan Shiksha Ki – primers (first reading books) and guidelines."),
    "/primers.php": ("D", None, "Primers – first reading books in many Indian languages (NCERT & CIIL)."),
    "/primersbirsa.php": ("D", None, "Primers in tribal languages."),
    "/adulteducation.php": ("D", None, "Adult education (ULLAS) – literacy material for adults who never went to school."),
    "/ptaw.php": ("D", "Wellbeing & safety", "‘Priya – The Accessibility Warrior’: an e-comic that teaches children about disability and accessibility."),
    "/komal-video.php": ("D", "Wellbeing & safety", "KOMAL – a film that teaches children to recognise and report sexual abuse."),
    "/healthandwell.php": ("D", "Wellbeing & safety", "School Health & Wellness programme – lessons and videos on health, emotions, safety."),
    "/manodarpan.php": ("D", "Wellbeing & safety", "Manodarpan – mental-health and emotional-wellbeing support for students (counselling, helpline, resources)."),
    "/eraksha.php": ("D", "Wellbeing & safety", "e-Raksha – awareness on cyber/online safety."),
    "/careerguide.php": ("D", "Career, money & opportunity", "Career Guide for school students – career options and how to reach them."),
    "/national-talent-examination.php": ("D", "Career, money & opportunity", "National Talent Search Exam (NTSE) – national scholarship exam for talented students: notices, papers, results."),
    "/model-question-papers.php": ("D", "Thinking & creativity", "Model question papers for exam practice."),
    "/chandrayaan.php": ("D", "Thinking & creativity", "Chandrayaan Utsav – special learning modules on India's moon mission for students, in many languages."),
    "/jn-national-science-exhibition.php": ("D", "Thinking & creativity", "Rashtriya Bal Vaigyanik Pradarshani (RBVP) – national children's science exhibition where students show their own projects."),
    "/kala-utsav.php": ("D", "Skill", "Kala Utsav – national arts festival where school students perform/compete in music, dance, theatre and visual arts."),
    "/bs-2021.php": ("D", None, "Bhasha Sangam – learn simple everyday sentences in 22 Indian languages (videos)."),
    "/e_jaaduipitara.php": ("D", None, "e-Jaadui Pitara – digital version of the play-based learning kit for children aged 3–8."),
    "/g20.php": ("D", None, "G20 reading materials for students."),
    "/newlaws2023.php": ("D", None, "Learning modules explaining India's new criminal laws of 2023 (BNS, BNSS, BSA)."),
    "/special_modules.php": ("D", None, "Special learning modules (e.g. Virasat & Vikas) on national themes for students."),
    "/viksit_bharat.php": ("D", None, "Viksit Bharat – special learning material on the theme of a developed India."),
    "/narishakti.php": ("D", None, "Nari Shakti Vandan – special learning material on women's empowerment."),
    "/birsa_munda.php": ("D", None, "Material on Birsa Munda, tribal freedom fighter."),
    "/r3_learning_resources.php": ("D", None, "R3 language-learning resources – selector for books that teach Indian languages."),
    "/trilingual_dictionaries.php": ("D", None, "Trilingual dictionaries (e.g. history terms in English–Hindi–Urdu)."),
    "/trilingual_dictionary_history.php": ("D", None, "Trilingual dictionary of history terms."),
    "/aac2021.php": ("T", None, "Alternative Academic Calendar 2021-22 – week-by-week learning activities for teachers/parents to do with children at home (made for COVID school closures)."),
    "/alternative-academic-calendar.php": ("T", None, "Alternative Academic Calendar – week-by-week learning activities for teachers/parents to do with children at home."),
    "/learning-outcome.php": ("T", None, "Learning Outcomes – what a child should be able to do at the end of each class; a yardstick for teachers and parents."),
    "/learning_outcomes.php": ("T", None, "Video message on implementing Learning Outcomes."),
    "/rationalised-content.php": ("T", None, "List of topics removed or reduced from textbooks (rationalisation) – tells teachers and students what is out of the syllabus."),
    "/syllabus_nep.php": ("T", None, "Syllabus documents – what is to be taught in each subject and class."),
    "/teacher-innovation-awards.php": ("T", None, "Awards recognising teachers who innovate in classrooms."),
    "/teacher-innovation.php": ("T", None, "Promoting Teacher Innovation programme."),
    "/shikshak-parv.php": ("T", None, "Shikshak Parv – teachers' festival with talks and workshops."),
    "/seminar.php": ("T", None, "Seminars, conferences and workshops – professional events for educators."),
    "/archive-seminar.php": ("T", None, "Archive of past seminars/conferences."),
    "/webinar_series.php": ("T", None, "‘Listen and Learn’ webinar series – recorded expert talks, mainly for teachers and educators."),
    "/iwtg.php": ("T", None, "International webinar on toys and games for learning (for educators)."),
    "/dcgc.php": ("T", "Wellbeing & safety", "Diploma Course in Guidance & Counselling – trains teachers to work as school counsellors."),
    "/smc2026.php": ("T", None, "School Management Committee (SMC) material – for parents and community members who oversee a school."),
    "/memo_lect_series.php": ("T", None, "Memorial lecture series (talks by eminent educationists)."),
    "/assistech.php": ("P", None, "Assistech 2022 – event/exhibition on assistive technology for children with disabilities."),
    "/focus-group.php": ("S", None, "National Curriculum Frameworks (NCF) and National Focus Group position papers – the blueprint of what and how students learn."),
    "/mandate-ncf.php": ("S", None, "Mandate documents for developing the National Curriculum Framework (2022)."),
    "/nep.php": ("S", None, "National Policy on Education documents."),
    "/policy-framework.php": ("S", None, "National Education Policy (NEP) and National Curriculum Framework (NCF) documents."),
    "/nas.php": ("S", None, "National Achievement Survey (NAS) – nation-wide test of a sample of students to measure how much they learn."),
    "/nas_offline.php": ("S", None, "Software package for correcting NAS survey data (for survey officials)."),
    "/nas_training.php": ("S", None, "NAS 2017 training material for survey staff."),
    "/nascycle2material.php": ("S", None, "Material for NAS Class X survey (cycle 2)."),
    "/drc.php": ("S", None, "District Report Cards – NAS learning results for each district."),
    "/drc_2021.php": ("S", None, "NAS 2021 District Report Cards – learning levels in each district."),
    "/drc_2021_asp.php": ("S", None, "NAS 2021 report cards for Aspirational (backward) Districts."),
    "/drc_aspirational.php": ("S", None, "NAS 2017 report cards for Aspirational Districts."),
    "/drcx.php": ("S", None, "NAS Class X District Report Cards."),
    "/src.php": ("S", None, "NAS State Reports."),
    "/src_2021.php": ("S", None, "NAS 2021 State Report Cards."),
    "/srcx.php": ("S", None, "NAS Class X State Report Cards."),
    "/fls.php": ("S", None, "Foundational Learning Study – survey of how well Class 3 children read and do basic maths."),
    "/fls_statereport.php": ("S", None, "Foundational Learning Study – state reports."),
    "/all-india-school-education-survey.php": ("S", None, "All India School Education Survey (AISES) – census of schools, teachers and facilities."),
    "/educational-survey.php": ("S", None, "Educational surveys conducted by NCERT."),
    "/research-grants-(eric).php": ("S", None, "ERIC – NCERT's grants for research in education (for researchers)."),
    "/ncf_mandate_gallery.php": ("P", None, "Photo gallery of NEP-2020 implementation events."),
    "/rbvp_gallery.php": ("P", None, "Photo gallery of the national children's science exhibition (RBVP)."),
    "/ncert-news.php": ("P", None, "NCERT in the news – newspaper coverage."),
    "/foundationday.php": ("P", None, "NCERT Foundation Day event page."),
    "/international-yoga.php": ("P", None, "International Yoga Day event page and photos."),
    "/constitution_day.php": ("P", None, "Constitution Day event page."),
    "/g_20.php": ("P", None, "G20-related event page."),
    "/archive-jnnsmee.php": ("P", None, "Archive of the children's national science, maths & environment exhibition."),
    # ---- other folders ----
    "/desm/b-ed-textbooks.php": ("T", None, "Textbooks for B.Ed (the degree that trains school teachers)."),
    "/desm/material-for-teachers.php": ("T", None, "Material for teachers – e.g. source books on assessment for Classes 6–8."),
    "/desm/schoolsciencejournal.php": ("T", None, "‘School Science’ journal – articles for science teachers (and senior students)."),
    "/desm/env-edu.php": ("D", None, "Project books on environmental education for Classes 6–12."),
    "/desm/workbook.php": ("D", None, "Workbooks for students."),
    "/desm/prayaas.php": ("D", "Thinking & creativity", "PRAYAAS – scheme that funds school students to do their own research projects."),
    "/desm/ras.php": ("D", "Thinking & creativity", "RAS – Rashtriya Avishkar Saptah (science & maths activity week for students)."),
    "/desm/facilities.php": ("O", None, "Facilities (labs etc.) of the Science & Maths department."),
    "/desm/resume-activities.php": ("S", None, "Summary of the Science & Maths department's activities."),
    "/dess/npep.php": ("S", None, "National Population Education Project – its faculty and work."),
    "/dess/aep.php": ("T", "Wellbeing & safety", "Adolescence Education Programme – training and resource material on adolescent health and life skills."),
    "/dess/dess-trilingual-dictionary.php": ("D", None, "DAISY (talking-book) trilingual history dictionary – full text + audio, usable by visually impaired students."),
    "/dess/dess.php": ("O", None, "Faculty of the Social Sciences department."),
    "/degsn/minority-cell.php": ("O", None, "Minority Cell of the special-needs department."),
    "/degsn/ncertbarkhaseries/start.html": ("D", None, "Barkha – digital graded story-readers for early readers (with audio and sign-language video)."),
    "/degsn/ncertbarkhaseries/help.html": ("D", None, "How to use the digital Barkha story-readers."),
    "/dee/ncertbarkhaseries/start.html": ("D", None, "Barkha – digital graded story-readers for early readers."),
    "/dee/ncertbarkhaseries/help.html": ("D", None, "How to use the digital Barkha story-readers."),
    "/dee/barkha-series.php": ("D", None, "Barkha series – graded story books that help young children learn to read."),
    "/dee/firkee-magazine.php": ("D", "Thinking & creativity", "Firkee Bachchon Ki – NCERT's magazine for children (stories, poems, art by and for kids)."),
    "/dee/bridge-course-package.php": ("T", None, "Bridge course package – teacher material to help children fill learning gaps."),
    "/dee/cce-package.php": ("T", None, "CCE package – how teachers assess children continuously and comprehensively, not just by exams."),
    "/dee/cce.php": ("T", None, "Continuous & Comprehensive Evaluation (CCE) material for teachers."),
    "/dee/every_child.php": ("T", None, "‘Every Child Matters’ – quality handbook for primary schools."),
    "/dee/analysis.php": ("S", None, "Analysis of primary textbooks of several States (Bihar, UP, Chhattisgarh…)."),
    "/dee/report.php": ("S", None, "New reports/documents on elementary education."),
    "/dee/print-materials-archive.php": ("G", MIXED, "Archive of the Elementary Education department's printed materials."),
    "/del/bhashautsav.php": ("D", None, "Bharatiya Bhasha Utsav – celebration of Indian languages with learning activities."),
    "/del/bhashaghar.php": ("G", None, "Bhasha Ghar – language resource centre and its catalogue."),
    "/division/dek/jaaduipitaracontent.php": ("D", None, "Contents of Jaadui Pitara – the play-based learning kit for ages 3–8."),
    "/division/dek/kit-manuals.php": ("D", "Skill", "Manuals that explain how to use NCERT science/maths kits."),
    "/division/dek/details-of-educational-kits.php": ("G", "Skill", "Details of the educational kits NCERT designs (science, maths, toys)."),
    "/division/dek/how-get-kits.php": ("G", "Skill", "How schools can obtain NCERT kits – delivery channel."),
    "/division/dek/details-of-kits-supplied.php": ("S", "Skill", "Record of kits supplied to each State/UT – evidence of delivery."),
    "/division/dek/specification_documents.php": ("O", None, "Technical specifications of kits (for manufacturers/suppliers)."),
    "/division/dek/ongoing-development.php": ("S", "Skill", "Kits currently being developed."),
    "/division/dek/brochure.php": ("O", None, "Brochure of the Educational Kits division."),
    "/division/der/basic_education.php": ("T", None, "‘Basics in Education’ – a textbook for B.Ed (teacher training)."),
    "/division/der/modules_material.php": ("T", None, "Modules for the online course on Action Research (teachers studying their own classrooms)."),
    "/division/der/ncertra.php": ("S", None, "Research abstracts of DIETs, SCERTs and NCERT units."),
    "/parakh/index.php": ("S", None, "PARAKH – national assessment centre that sets standards for exams/assessment across school boards."),
    "/parakh/about.php": ("S", None, "About PARAKH, the national assessment centre."),
    "/parakh/hpc.php": ("T", None, "Holistic Progress Card (HPC) – new report card that records a child's all-round growth; filled by teacher, child and parent."),
    "/parakh/rashtriyasarvekshan.php": ("S", None, "PARAKH Rashtriya Sarvekshan 2024 – national survey of student learning."),
    "/parakh/seas.php": ("S", None, "State Educational Achievement Survey (SEAS)."),
    "/parakh/equivalenceboard.php": ("S", None, "Equivalence of school boards – which boards' certificates are treated as equal."),
    "/parakh/skill_edu.php": ("S", None, "Assessment framework for skill education."),
    "/parakh/resources.php": ("S", None, "PARAKH resources (assessment documents)."),
    "/parakh/sample_questions.php": ("D", "Thinking & creativity", "Sample assessment questions."),
    "/parakh/faqs.php": ("O", None, "FAQs about PARAKH."),
    "/parakh/advisory-board.php": ("S", None, "PARAKH's assessment programmes – NAS, SEAS, Foundational Literacy & Numeracy."),
    "/division/pd/children-books.php": ("G", None, "Children's books published by NCERT."),
    "/division/pd/online-textbook.php": ("G", None, "Online textbooks."),
    "/division/pd/list-publication.php": ("G", MIXED, "List of NCERT publications."),
    "/division/pd/journals-periodicals.php": ("G", MIXED, "Journals and periodicals."),
    "/division/pd/info-customers.php": ("G", None, "Information for book buyers – prices, how and where to buy NCERT books."),
    "/division/pd/activities.php": ("O", None, "Activities of the Publication Division."),
    "/division/pd/people.php": ("O", None, "Staff of the Publication Division."),
    "/cncl/index.php": ("G", None, "Home of CNCL (National Literacy Centre-Cell) – runs ULLAS, literacy for adults who missed school."),
    "/cncl/ullas.php": ("G", None, "About ULLAS (New India Literacy Programme) – reading, writing, numeracy and life skills for adults 15+."),
    "/cncl/praveshika.php": ("D", None, "ULLAS primers – first reading/writing books for adult learners."),
    "/cncl/story_book.php": ("D", None, "Story books for new adult readers (ULLAS)."),
    "/cncl/primer_audiobooks.php": ("D", None, "Audio-book versions of the ULLAS primers."),
    "/cncl/worksheet.php": ("D", None, "Literacy and numeracy worksheets for adult learners."),
    "/cncl/ltm.php": ("D", None, "Learning & teaching materials for adult literacy."),
    "/cncl/def_explore.php": ("D", None, "ULLAS material in different Indian languages."),
    "/cncl/ce_edu.php": ("D", None, "Study material – continuing education for adults."),
    "/cncl/obe-program.php": ("D", None, "Study material – basic education for adults."),
    "/cncl/vsd.php": ("D", "Career, money & opportunity", "Study material – vocational skill development for adults."),
    "/cncl/animated_videos.php": ("D", None, "Animated learning videos for adult learners."),
    "/cncl/cls_audio_program.php": ("D", "Wellbeing & safety", "Audio lessons on critical life skills (health, money, digital, legal awareness) for adult learners."),
    "/cncl/cls_video_program.php": ("D", "Wellbeing & safety", "Video lessons on critical life skills for adult learners."),
    "/cncl/ce_audio_program.php": ("D", None, "Audio lessons – continuing education for adults."),
    "/cncl/ce_edu_video_program.php": ("D", None, "Video lessons – continuing education for adults."),
    "/cncl/bedu_video_program.php": ("D", None, "Video lessons – basic education for adults."),
    "/cncl/fln_video_programs.php": ("D", None, "Video lessons – foundational literacy & numeracy for adults."),
    "/cncl/vsd_video_program.php": ("D", "Career, money & opportunity", "Video lessons – vocational skills for adults."),
    "/cncl/margdarshika.php": ("T", None, "Guidebook for volunteer teachers who teach adult learners."),
    "/cncl/guidelines_primer.php": ("S", None, "Guidelines for writing literacy primers."),
    "/cncl/live_sessions.php": ("T", None, "Live interactive sessions (for volunteers and learners)."),
    "/cncl/los.php": ("T", None, "Learning outcomes for adult literacy."),
    "/cncl/assessment.php": ("D", "Thinking & creativity", "Assessment items for adult learners."),
    "/cncl/test_papers.php": ("D", "Thinking & creativity", "Test papers for adult learners."),
    "/cncl/disaster-management.php": ("D", "Wellbeing & safety", "Disaster management learning material."),
    "/cncl/policy_docs.php": ("S", None, "Policy documents on literacy."),
    "/cncl/cncl_docs.php": ("S", None, "CNCL documents."),
    "/cncl/compendium.php": ("S", None, "Compendium (collection of literacy documents)."),
    "/cncl/workshop_reports.php": ("S", None, "Reports of CNCL workshops."),
    "/cncl/open_files.php": ("S", None, "Open files / documents of CNCL."),
    "/cncl/genesis.php": ("O", None, "How CNCL began."),
    "/cncl/mission.php": ("O", None, "Mission of CNCL."),
    "/cncl/vision.php": ("O", None, "Vision of CNCL."),
    "/cncl/notifications.php": ("O", None, "CNCL notices."),
    "/cncl/press-release.php": ("P", None, "CNCL press releases."),
    "/cncl/gallery.php": ("P", None, "CNCL photo gallery."),
    "/cncl/audio-gallery.php": ("G", None, "CNCL audio gallery (adult-literacy audio lessons)."),
    "/cncl/video-gallery.php": ("G", None, "CNCL video gallery."),
    "/cncl/office-staffs.php": ("O", None, "CNCL office staff."),
    "/tamanna/index.html": ("D", "Career, money & opportunity", "TAMANNA – aptitude test for Class 9–10 students to discover strengths before choosing subjects/careers."),
    "/cells/hc/tamanna/index.html": ("D", "Career, money & opportunity", "TAMANNA – aptitude test for Class 9–10 students to discover strengths before choosing subjects/careers."),
    "/cncl/tamanna/index.html": ("D", "Career, money & opportunity", "TAMANNA – aptitude test for Class 9–10 students to discover strengths before choosing subjects/careers."),
    "/qmts/index.php": ("S", None, "Quality Monitoring Tools (QMTs) – formats States use to check quality of elementary schools; state reports."),
    "/programmes/education_survey/7_survey_reports.html": ("S", None, "7th All India School Education Survey reports."),
    "/programmes/education_survey/atlas.html": ("S", None, "Atlas of school education (maps of school facilities)."),
}

# Standard pages that every department/division mini-site has (matched on file name)
DEPT_FILES = {
    "index.php": ("O", "Home page of this department/unit – describes its work and links to its materials."),
    "faculty-members.php": ("O", "List of the department's academic staff."),
    "administration.php": ("O", "Office/administrative staff of the department."),
    "office-staff.php": ("O", "Office staff of the department."),
    "people.php": ("O", "Staff of this unit."),
    "staff.php": ("O", "Staff of this unit."),
    "contact-us.php": ("O", "Contact details."),
    "advisory-board.php": ("O", "Advisory board – experts who guide the department."),
    "screen-reader.php": ("O", "Help page for blind users using screen-reader software."),
    "committee.php": ("O", "Committee of this unit."),
    "circular.php": ("O", "Office circulars."),
    "announcement.php": ("O", "Announcements of this unit."),
    "disclo_un_rti.php": ("O", "RTI disclosure of this unit."),
    "current-projects.php": ("S", "Projects the department is working on now (studies, material development, training plans) – outcomes reach students later."),
    "past-projects.php": ("S", "Projects completed by the department in earlier years."),
    "other-activities.php": ("S", "Other activities of the department (events, collaborations)."),
    "activities.php": ("S", "Activities of this unit."),
    "research.php": ("S", "Research done by the department."),
    "research-work.php": ("S", "Research work of this division."),
    "print-materials.php": ("G", "Shelf of books/documents made by the department – a mix of student material and teacher resources."),
    "non-print-materials.php": ("G", "Shelf of audio/video/digital material made by the department."),
    "publication.php": ("G", "Publications of this unit."),
    "gallery.php": ("P", "Photo gallery of the department's events."),
    "image_gallery.php": ("P", "Photo gallery."),
    "krp.php": ("T", "Key Resource Persons – experts who train teachers in their state."),
    "master-trainers.php": ("T", "Master Trainers – teachers trained to train other teachers."),
    "srg.php": ("T", "State Resource Groups – state-level teams that train teachers."),
    "ict-initiatives.php": ("G", "Digital initiatives of this unit."),
}

# Folder-level defaults (prefix of path) -> (role, product or None, note)
FOLDERS = [
    ("/pdf/publication/journalsandperiodicals/journalofindianeducation/", "S", None, "Journal of Indian Education – NCERT research journal on education (for researchers & teacher educators)."),
    ("/pdf/publication/journalsandperiodicals/indianeducationalreview/", "S", None, "Indian Educational Review – NCERT research journal (for researchers)."),
    ("/pdf/publication/journalsandperiodicals/bhartiyaadhunikshiksha/", "S", None, "Bhartiya Adhunik Shiksha – NCERT's Hindi journal on education (for researchers & educators)."),
    ("/pdf/publication/journalsandperiodicals/indianjournalofeducationaltechnology/", "S", None, "Indian Journal of Educational Technology – NCERT/CIET research journal."),
    ("/pdf/publication/journalsandperiodicals/schoolscience/", "T", None, "School Science – NCERT journal for science teachers (and senior students)."),
    ("/pdf/publication/journalsandperiodicals/theprimaryteacher/", "T", None, "The Primary Teacher – NCERT journal for primary-school teachers."),
    ("/pdf/publication/journalsandperiodicals/prathmikshikshak/", "T", None, "Prathmik Shikshak – NCERT's Hindi journal for primary-school teachers."),
    ("/pdf/publication/journalsandperiodicals/vtte/", "T", None, "Voices of Teachers and Teacher Educators – NCERT journal written by and for teachers."),
    ("/ldd/services/pressclips/", "P", None, "Press clippings – newspaper coverage collected by the NCERT library."),
    ("/ncertldd/services/pressclip", "P", None, "Press clippings – newspaper coverage collected by the NCERT library."),
    ("/cncl/resources/pdf/", "S", None, "CNCL document / report (literacy programme)."),
    ("/cncl/resources/workshop_reports", "S", None, "Report of a CNCL workshop (developing literacy material)."),
    ("/guesthouse/", "O", None, "NCERT Guest House & PG hostel – booking, rules, committee."),
    ("/sections/vls/", "O", None, "Vigilance & Legal Section – anti-corruption and legal matters of NCERT."),
    ("/cells/hc/", "O", None, "Hindi Cell – promotes use of Hindi in NCERT's official work."),
    ("/ldd/", "S", None, "NCERT Library & Documentation Division – library services for researchers and staff (catalogue, journals, rules)."),
    ("/ncertldd/images/", "P", None, "Photo from the NCERT library website."),
    ("/ncertldd/", "S", None, "NCERT Library website – library services for researchers and staff."),
    ("/ncert/collection/", "S", None, "NCERT Library – journal collection lists (for researchers)."),
    ("/qmts/", "S", None, "Quality Monitoring Tools – formats and State reports for checking quality of elementary schools."),
    ("/statebooks/", "D", None, "Textbook of a State/UT board as an e-book (ePub)."),
    ("/cncl/resources/", "D", None, "ULLAS learning material for adult learners (primer, worksheet, story book…)."),
    ("/cncl/gallery/", "P", None, "Photo from CNCL events."),
    ("/pdf/chandrayan/", "D", "Thinking & creativity", "Chandrayaan learning module for students (this language)."),
    ("/pdf/bridge_programme/", "D", None, "Bridge Programme booklet – helps students move to the new NCF-based textbooks."),
    ("/pdf/bridge_month_program/", "D", None, "Bridge month programme material."),
    ("/pdf/primer/", "D", None, "Primer – first reading book in an Indian language."),
    ("/pdf/module/", "D", None, "Special learning module for students."),
    ("/pdf/e_jaaduipitara/", "D", None, "Jaadui Pitara learning material (ages 3–8)."),
    ("/pdf/school-kit/", "D", "Skill", "School kit manual."),
    ("/pdf/announcement/vacancies/", "O", None, "Job vacancy / recruitment document."),
    ("/pdf/nas/", "S", None, "National Achievement Survey document (learning levels of students)."),
    ("/pdf/fls/", "S", None, "Foundational Learning Study report."),
    ("/pdf/annualreport/", "O", None, "NCERT annual report."),
    ("/pdf/annualaccounts/", "O", None, "NCERT annual accounts."),
    ("/pdf/rti/", "O", None, "RTI disclosure document."),
    ("/pdf/management/", "O", None, "Governance document (committee minutes, rules)."),
    ("/pdf/programmeadvisorycommittee/", "O", None, "Programme Advisory Committee document."),
    ("/pdf/focus-group/", "S", None, "National Focus Group position paper / curriculum framework."),
    ("/pdf/nep/", "S", None, "National Education Policy document."),
    ("/pdf/biodata/", "O", None, "Biodata of an officer."),
    ("/uploads/news-content/", "P", None, "News clipping image."),
    ("/images/", "P", None, "Event photo."),
    ("/division/ird/", "O", None, "International Relations Division – NCERT's cooperation with other countries."),
    ("/division/pmd/", "O", None, "Planning & Monitoring Division – plans and tracks NCERT's own programmes and budget."),
    ("/textbook/", "G", None, "Textbook-related file."),
]

# Generic rules on path + link text (first match wins) -> (role, note)
RULES = [
    ("O", "Tender / purchase notice for vendors (printing, equipment, works).", r"tender|corrigend|\bbids?\b|quotation|\beoi\b|e-?procure|निविदा"),
    ("O", "Job vacancy, interview or recruitment result for NCERT staff – for job seekers, not learners.", r"vacanc|recruit|walk.?in|interview|project.?staff|deputation|empanel|shortlist|waitlist|rejected|eligible.?candidates|admit.?card|भर्ती|रिक्ति|साक्षात्कार"),
    ("O", "Finance record (accounts, pension, insurance, salary).", r"pension|insurance|annual.?account|gpf|salary|budget|पेंशन|बीमा"),
    ("O", "RTI / legal disclosure document.", r"\brti\b|disclo"),
    ("O", "List of book agents blacklisted by NCERT (for book sellers/buyers).", r"blacklist"),
    ("O", "NCERT annual report – record of the organisation's yearly work.", r"annual.?report|वार्षिक प्रतिवेदन|वार्षिक रिपोर्ट"),
    ("G", "Catalogue / list of publications – tells what books exist and their prices.", r"catalogue|checklist|list.?of.?publication|price.?list"),
    ("O", "Governance record – committee meeting minutes, rules, orders.", r"minutes|meeting|executive.?commit|finance.?commit|building.?(and|&).?works|कार्यवृत्त|बैठक"),
    ("D", "Programme / competition / opportunity for students.", r"prayaas|olympiad|\bntse\b|talent.?search|kala.?utsav|\brbvp\b|bal.?vaigyanik|science.?exhibition|tamanna|career|scholarship|competition|प्रतियोगिता|विज्ञान प्रदर्शनी"),
    ("P", "Photo / news / publicity of an event.", r"gallery|press.?(release|clip)|pressclip|news|coffee.?table|photos?\b|समाचार|झलकियां"),
    ("S", "Survey / monitoring / research document – measures or studies the education system.", r"\bnas\b|\breports?\b|रिपोर्ट|प्रतिवेदन|national.?study|curriculum.?review|कर्रिकुलम|achievement.?survey|survey|aises|report.?card|\bdrc\b|\bsrc\b|\bfls\b|monitoring|evaluation|research|abstract|study|studies|सर्वेक्षण|शोध|अनुसंधान"),
    ("S", "Curriculum / policy blueprint – decides what and how students learn.", r"\bncf|curriculum.?framework|position.?paper|focus.?group|policy|framework|\bnep\b|mandate|guideline|पाठ्यचर्या|नीति|दिशा"),
    ("T", "Material for teachers / teacher education / training.", r"teacher|teaching|training|trainer|inset|reflective|pindics|learning.?outcome|handbook|source.?book|margdarshika|\bcce\b|pedagog|b\.?ed\b|d\.?el\.?ed|action.?research|nishtha|\bcpd\b|orientation|शिक्षक|प्रशिक्षण|अध्यापक|शिक्षण|टीचर|टीचिंग|हैंडबुक|ट्रेनिंग|इनसेट|सीखने के प्रतिफल"),
    ("T", "Professional event for educators (seminar, conference, workshop, webinar).", r"seminar|conference|workshop|webinar|lecture|संगोष्ठी|सम्मेलन|कार्यशाला"),
    ("O", "Office notice / circular / order.", r"notice|circular|\border\b|office.?memo|notification|सूचना|परिपत्र|आदेश"),
]
RULES = [(r, n, re.compile(x, re.I)) for r, n, x in RULES]

# External sites (host suffix) -> (role, product or None, note)
EXTERNAL = [
    ("epathshala.nic.in", "G", MIXED, "ePathshala – NCERT's free app/portal with e-textbooks, audio, video for students, teachers and parents."),
    ("diksha.gov.in", "G", MIXED, "DIKSHA – national digital platform with QR-linked lessons, videos and teacher courses."),
    ("swayam.gov.in", "G", MIXED, "SWAYAM – free online courses (including NCERT courses for Classes 11–12 and teachers)."),
    ("swayamprabha.gov.in", "G", MIXED, "SWAYAM Prabha – free educational DTH TV channels."),
    ("ciet.nic.in", "G", MIXED, "CIET – NCERT's Central Institute of Educational Technology (e-content, TV/radio, PM eVidya)."),
    ("ciet.ncert.gov.in", "G", MIXED, "CIET – NCERT's Central Institute of Educational Technology (e-content, TV/radio, PM eVidya)."),
    ("ncertx.in", "G", MIXED, "NCERT-X – NCERT's online learning platform."),
    ("ndl.education.gov.in", "G", MIXED, "National Digital Library of India – free digital books and resources."),
    ("ncertbooks.ncert.gov.in", "G", None, "Official site to buy NCERT books online – delivery channel."),
    ("amazon.in", "G", None, "Buy NCERT books on Amazon – delivery channel."),
    ("play.google.com", "G", MIXED, "Mobile app on Google Play (NCERT/education app)."),
    ("mycareeradvisor.ncert.gov.in", "D", "Career, money & opportunity", "My Career Advisor – career guidance app/portal for students."),
    ("sathee.prutor.ai", "D", "Career, money & opportunity", "SATHEE – free coaching for competitive exams (JEE, NEET…)."),
    ("kalautsav.ncert.gov.in", "D", "Skill", "Kala Utsav portal – students' national arts festival."),
    ("ullas.education.gov.in", "D", None, "ULLAS portal – literacy for adults."),
    ("skillindiadigital.gov.in", "D", "Career, money & opportunity", "Skill India Digital – skill courses and jobs."),
    ("prerana.education.gov.in", "D", None, "PRERANA – experiential learning programme for students."),
    ("hpc.parakh.ncert.gov.in", "T", None, "Holistic Progress Card portal (filled by teachers/students/parents)."),
    ("itpd.ncert.gov.in", "T", None, "Online teacher professional-development courses."),
    ("ictaward.ncert.gov.in", "T", None, "National ICT awards for teachers."),
    ("ictcurriculum.gov.in", "T", None, "ICT curriculum for students and teacher educators."),
    ("cee.ncert.gov.in", "T", None, "Entrance exam for teacher-education courses at NCERT's Regional Institutes."),
    ("dcgc.ncert.org.in", "T", "Wellbeing & safety", "Diploma Course in Guidance & Counselling portal (for teachers)."),
    ("riea", "T", None, "Regional Institute of Education – NCERT college that trains teachers."),
    ("rieb", "T", None, "Regional Institute of Education – NCERT college that trains teachers."),
    ("riem", "T", None, "Regional Institute of Education – NCERT college that trains teachers."),
    ("nerie.nic.in", "T", None, "North-East Regional Institute of Education – NCERT college that trains teachers."),
    ("psscive", "G", "Career, money & opportunity", "PSSCIVE – NCERT's vocational education institute (job-skill curricula, textbooks)."),
    ("journals.ncert.gov.in", "S", None, "NCERT research journals online."),
    ("osre.ncert.gov.in", "S", None, "NCERT online survey/research portal."),
    ("aises.nic.in", "S", None, "All India School Education Survey portal."),
    ("ntse.ncert.gov.in", "D", "Career, money & opportunity", "NTSE – national scholarship exam portal."),
    ("forms.ncert.gov.in", None, None, "Online form (registration / application)."),
    ("docs.google.com", None, None, "Google document / form."),
    ("forms.gle", None, None, "Google form (registration / submission)."),
    ("digialm.com", "O", None, "Online exam platform used for NCERT recruitment tests."),
    ("samarth.edu.in", "O", None, "Samarth – online recruitment/administration portal."),
    ("nvda-project.org", "O", None, "Free screen-reader software (accessibility help for blind users)."),
    ("freedomscientific.com", "O", None, "Screen-reader software (accessibility help)."),
    ("gwmicro.com", "O", None, "Screen-reader software (accessibility help)."),
    ("satogo.com", "O", None, "Screen-reader software (accessibility help)."),
    ("yourdolphin.co.uk", "O", None, "Screen-reader software (accessibility help)."),
    ("pgportal.gov.in", "O", None, "Public grievance portal of the Government of India."),
    ("rti.nic.in", "O", None, "RTI portal of the Government of India."),
    ("cic.gov.in", "O", None, "Central Information Commission (RTI appeals)."),
    ("timesofindia.indiatimes.com", "P", None, "News coverage."),
    ("indianexpress.com", "P", None, "News coverage."),
    ("deccanherald.com", "P", None, "News coverage."),
    ("amarujala.com", "P", None, "Newspaper link."),
    ("facebook.com", "P", None, "NCERT on social media."),
    ("twitter.com", "P", None, "NCERT on social media."),
    ("x.com", "P", None, "NCERT on social media."),
    ("instagram.com", "P", None, "NCERT on social media."),
    ("linkedin.com", "P", None, "NCERT on social media."),
]

SOCIAL_VIDEO = re.compile(r"(youtube\.com|youtu\.be)$")


def _path(u):
    p = urlsplit(u)
    return p.hostname or "", (p.path or "/").lower(), p.query


def _words(path):
    """'/dte/pdf/Summary_report-2013%20x.pdf' -> '/dte/pdf/summary report 2013 x pdf' so \\b word rules match."""
    return re.sub(r"%20|[_\-.]+", " ", path)


def _product(hay, given=None):
    if given:
        return given
    for name, rx in PRODUCT_RX:
        if rx.search(hay):
            return name
    return "Knowledge"


def _page_rule(path, segs):
    if path in PAGES:
        return PAGES[path]
    fname = segs[-1] if segs else ""
    in_dept = len(segs) >= 2 and not path.startswith(("/pdf/", "/uploads/", "/images/"))
    if in_dept and fname in DEPT_FILES:
        r, note = DEPT_FILES[fname]
        return (r, None, note)
    return None


def _folder_rule(path):
    for prefix, r, prod, note in FOLDERS:
        if path.startswith(prefix):
            return (r, prod, note)
    return None


def assign(rows, urls):
    """Adds lens columns to every row (dict) in place."""
    by_url = {r["URL"]: r for r in rows}
    cache = {}
    final = {}   # url -> (role, product, note) once assigned

    def page_lens(u):
        """Lens of a page on ncert.nic.in (used for inheritance)."""
        if u in final:
            return final[u]
        if u in cache:
            return cache[u]
        host, path, _ = _path(u)
        segs = [s for s in path.split("/") if s]
        res = _page_rule(path, segs) or _folder_rule(path)
        if not res:
            row = by_url.get(u)
            hay = " ".join([_words(path), row["Link text"] if row else "", row["Page title"] if row else ""])
            for r, note, rx in RULES:
                if rx.search(hay):
                    res = (r, None, note)
                    break
        cache[u] = res
        return res

    def best_parent(u):
        rec = urls.get(u) or {}
        parents = [p for p in rec.get("found_on") or [] if p in urls]
        if not parents:
            return None
        # the most specific page = the one linked from the fewest other pages
        return min(parents, key=lambda p: (urls[p].get("found_on_count", 0), len(p)))

    pages_first = sorted(rows, key=lambda r: r["Type"] not in ("Web page", "Flipbook"))
    for row in pages_first:
        u = row["URL"]
        host, path, query = _path(u)
        segs = [s for s in path.split("/") if s]
        hay = " ".join([_words(path), query, row["Link text"], row["Page title"]]).lower()
        role = prod = note = None
        how = ""

        if host != "ncert.nic.in":
            for suffix, r, p, n in EXTERNAL:
                if host == suffix or host.endswith("." + suffix) or (suffix in host and "." not in suffix):
                    role, prod, note = r, p, n
                    break
            if role is None and SOCIAL_VIDEO.search(host):
                if re.search(r"/(@|c/|channel/|user/)", path) or path in ("/", ""):
                    role, note = "P", "NCERT's YouTube channel / social media page."
                else:
                    note = "YouTube video."
            if role is None and note is None and re.search(r"\.(gov|nic)\.in$|\.gov$|mygov\.in$|g20\.in$", host):
                role, prod, note = "X", NONE, "Government of India website (standard footer link)."
        else:
            res = _page_rule(path, segs) if row["Type"] in ("Web page", "Flipbook") else None
            res = res or _folder_rule(path)
            if res:
                role, prod, note = res
            else:
                for r, n, rx in RULES:
                    if rx.search(hay):
                        role, note = r, n
                        break

        # inherit from the page that lists it
        if role is None:
            par = best_parent(u)
            pl = page_lens(par) if par else None
            if pl:
                prole, pprod, pnote = pl
                role = "D" if prole == "G" else prole
                if prod is None and pprod not in (None, MIXED):
                    prod = pprod
                kind = "Video" if "youtu" in host else ("Item" if host == "ncert.nic.in" else "Link")
                where = urlsplit(par).path
                note = (note + " " if note else "") + (f"{kind} listed on {where} – {pnote.rstrip('.')}." if pnote else f"{kind} listed on {where}.")
                mixed_shelf = pprod == MIXED or where.endswith(
                    ("print-materials.php", "print-materials-archive.php", "other-publications.php", "list-publication.php"))
                how = "inherited from a mixed shelf – verify" if mixed_shelf else "inherited from linking page"

        # last resort: use the topic / type
        if role is None:
            t, ty = row["Topic"], row["Type"]
            if t in ("Recruitment & Vacancies", "Tenders & Procurement", "Pension, Insurance & Accounts",
                     "About NCERT & Administration", "Notices, Circulars & Orders"):
                role = "O"
            elif t == "Photo Gallery & News" or ty == "Image":
                role = "P"
            elif t in ("Research, Surveys & Monitoring", "Curriculum, Syllabus & Policy", "Library & Documentation Services"):
                role = "S"
            elif t in ("Teacher Education & Training", "Events, Competitions & Days") and "competition" not in hay:
                role = "T"
            elif host == "ncert.nic.in" and ty != "Web page":
                role = "D"
            elif host == "ncert.nic.in":
                role = "G"
            else:
                role = "X"
            how = "guessed from topic – please verify"
            note = note or {
                "O": "Administrative / office document.", "P": "Photo or publicity item.",
                "S": "System-level document (curriculum, survey, research).", "T": "Material for teachers / educators.",
                "D": "Learning material (document/media) on the NCERT site.", "G": "Page on the NCERT site.",
                "X": "Link to another website."}[role]

        if role in ("O", "P", "X"):
            prod = NONE
        else:
            prod = _product(hay, prod)
        final[u] = (role, prod if prod not in (NONE,) else None, note)
        row["Reaches learner"] = ROLE[role]
        row["Eventual product for learner"] = prod
        row["What it is / used for"] = note or ""
        row["Lens basis"] = how or "rule"


GLOSSARY = [
    ("NCERT", "National Council of Educational Research and Training – central body that writes national textbooks, curricula and trains teachers."),
    ("NEP 2020", "National Education Policy 2020 – the government policy that sets the direction for all education reform."),
    ("NCF", "National Curriculum Framework – the blueprint of what and how children learn. NCF-FS 2022 = Foundational Stage (ages 3–8); NCF-SE 2023 = School Education."),
    ("Focus Group / Position Paper", "Expert papers on each subject/theme written while preparing an NCF."),
    ("Rationalised content", "Topics removed or reduced from textbooks to lighten the syllabus."),
    ("Learning Outcomes (LOs)", "Statements of what a child should be able to do at the end of each class."),
    ("Bridge Programme / Bridge Course", "Short course that helps children catch up or move from old to new textbooks."),
    ("Exemplar Problems", "Extra, higher-order practice questions that go with NCERT textbooks."),
    ("Primer / Praveshika", "First reading book for beginners (children or adults), often in a mother tongue."),
    ("Barkha series", "Graded story-reader books that help young children learn to read; also available digitally."),
    ("Jaadui Pitara", "‘Magic box’ – play-based learning kit (toys, puzzles, story books) for ages 3–8; e-Jaadui Pitara is its digital version."),
    ("Firkee Bachchon Ki", "NCERT's magazine for children."),
    ("Sapnon Ki Udaan", "NCERT/Ministry of Education e-magazine for students aged 10–18 (PDF + flipbook issues)."),
    ("Kala Utsav", "National arts festival where school students perform and compete."),
    ("RBVP (earlier JNNSMEE)", "Rashtriya Bal Vaigyanik Pradarshani – national children's science exhibition."),
    ("PRAYAAS", "Scheme funding school students to carry out their own research projects."),
    ("NTSE", "National Talent Search Examination – national scholarship exam for students."),
    ("TAMANNA", "Try And Measure Aptitude And Natural Abilities – aptitude test for Class 9–10 students."),
    ("Manodarpan", "Ministry/NCERT initiative for students' mental health and emotional wellbeing."),
    ("CCE", "Continuous and Comprehensive Evaluation – assessing children throughout the year, not just in exams."),
    ("HPC", "Holistic Progress Card – new report card recording a child's all-round development."),
    ("PARAKH", "Performance Assessment, Review and Analysis of Knowledge for Holistic Development – NCERT's national assessment centre."),
    ("NAS", "National Achievement Survey – national test of a sample of students to measure learning levels by district/state."),
    ("SEAS", "State Educational Achievement Survey."),
    ("FLS", "Foundational Learning Study – survey of Class 3 reading and maths skills."),
    ("AISES", "All India School Education Survey – census of schools, teachers and facilities."),
    ("QMTs", "Quality Monitoring Tools – formats used by States to monitor elementary school quality."),
    ("DRC / SRC", "District / State Report Card (results of NAS)."),
    ("ERIC", "Educational Research and Innovations Committee – NCERT's research grants."),
    ("CIET", "Central Institute of Educational Technology (part of NCERT) – e-content, TV/radio, PM eVidya."),
    ("DIKSHA", "National digital platform for school education (QR-coded textbooks, videos, teacher courses)."),
    ("ePathshala", "NCERT's app/portal for e-textbooks and audio-video resources."),
    ("SWAYAM / SWAYAM Prabha", "Government online course platform / free educational TV channels."),
    ("NISHTHA", "National programme for in-service teacher training."),
    ("ULLAS", "Understanding Lifelong Learning for All in Society – New India Literacy Programme for adults (15+) who missed school."),
    ("CNCL", "Centre for National Literacy / National Literacy Centre-Cell at NCERT – runs ULLAS material."),
    ("Margdarshika", "Guidebook (here: for volunteer teachers of adult learners)."),
    ("LTM", "Learning and Teaching Materials."),
    ("Bhasha Sangam", "Programme to learn simple sentences in 22 Indian languages."),
    ("R3", "Language-learning resources (books for learning Indian languages)."),
    ("DEE", "Department of Elementary Education (Classes 1–8, early childhood)."),
    ("DESM", "Department of Education in Science and Mathematics."),
    ("DESS", "Department of Education in Social Sciences."),
    ("DEL", "Department of Education in Languages."),
    ("DEAA", "Department of Education in Arts and Aesthetics."),
    ("DEGSN", "Department of Education of Groups with Special Needs (disability, minorities, inclusion)."),
    ("DEPFE", "Department of Educational Psychology and Foundations of Education."),
    ("DGS", "Department of Gender Studies."),
    ("DTE", "Department of Teacher Education."),
    ("DCS / DCSD", "Department of Curriculum Studies (and Development)."),
    ("DEK", "Division of Educational Kits – designs science/maths kits and Jaadui Pitara."),
    ("DER", "Division of Educational Research."),
    ("ESD", "Educational Survey Division (runs AISES)."),
    ("PD", "Publication Division – prints and sells NCERT books."),
    ("IRD", "International Relations Division."),
    ("PMD", "Planning and Monitoring Division (plans NCERT's own programmes)."),
    ("LDD", "Library and Documentation Division."),
    ("OPAC", "Online Public Access Catalogue – the library's book search."),
    ("RIE", "Regional Institute of Education – NCERT colleges (Ajmer, Bhopal, Bhubaneswar, Mysuru, Shillong, Nellore) that train teachers."),
    ("PSSCIVE", "Pandit Sunderlal Sharma Central Institute of Vocational Education, Bhopal – NCERT's vocational-education institute."),
    ("PGDVET", "Post Graduate Diploma in Vocational Education and Training (course at PSSCIVE)."),
    ("DCGC", "Diploma Course in Guidance and Counselling – trains teachers as school counsellors."),
    ("SCERT / DIET", "State Council of Educational Research and Training / District Institute of Education and Training – state & district teacher-training bodies."),
    ("KRP / SRG / MT", "Key Resource Person / State Resource Group / Master Trainer – people who train other teachers."),
    ("SMC", "School Management Committee – parents and community members who oversee a government school."),
    ("B.Ed / D.El.Ed", "Teacher-training degree / diploma."),
    ("Action Research", "Teachers studying a problem in their own classroom and testing solutions."),
    ("PAC", "Programme Advisory Committee – approves NCERT's annual programmes."),
    ("RTI / PIO", "Right to Information Act / Public Information Officer who answers RTI requests."),
    ("Tender / Corrigendum", "Notice inviting vendors to bid for a contract / correction to such a notice."),
    ("Flipbook", "A PDF shown as a page-turning online book."),
    ("ePub", "E-book file format (reflowable text, works on phones/e-readers)."),
]
