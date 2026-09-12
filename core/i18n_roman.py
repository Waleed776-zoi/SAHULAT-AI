"""
Roman Urdu strings (P2-1) — Urdu language, Latin script.

WHY THIS IS A SEPARATE FILE
    Adding a third key to 445 literals would bury the English/Urdu pairs the
    product actually promises. Keeping Roman Urdu in its own table leaves
    those pairs reviewable side by side, and a missing entry here degrades to
    English rather than breaking a page.

HOW THESE ARE WRITTEN
    As Pakistanis actually type, not as a transliteration exercise. Roman Urdu
    in practice borrows English freely for terms that have no everyday Urdu
    equivalent — "scholarship", "documents", "profile", "deadline" — and
    forcing literary Urdu words into Latin script would read as stilted to the
    very people this mode exists for.

    Placeholders ({n}, {percent}, …) are identical to the English string. A
    test asserts that for every key, because a dropped placeholder turns a
    sentence into a crash at render time.
"""
from __future__ import annotations

from typing import Dict

ROMAN: Dict[str, str] = {
    # -- shell -------------------------------------------------------------
    "app_title": "Sahulat AI",
    "app_subtitle": "Pakistan Opportunity aur Services Navigator",
    "app_tagline": "Scholarships, jobs aur training dhoondein jin ke liye aap eligible ho "
                   "sakte hain — ya koi ad upload kar ke poochein.",
    "disclaimer_banner": "Sahulat AI sirf maloomat ke liye pre-screening tool hai, koi "
                         "sarkari service nahi. Aakhri eligibility ka faisla metaaliqa "
                         "idare ke official channel se confirm karein.",
    "chip_no_cnic": "CNIC ya naam nahi poocha jata",
    "chip_rules_based": "Rules par mabni, andaza nahi",
    "chip_official_sources": "Official sources se juda hua",
    "chip_bilingual": "English aur Urdu",
    "tab_find": "Mauqe dhoondein",
    "tab_upload": "Ad parhwayein",
    "tab_how": "Yeh kaise kaam karta hai",
    "step_1_title": "Chunein aap kya dhoond rahe hain",
    "step_2_title": "Apne baare mein batayein",
    "step_3_title": "Apne natayij dekhein",
    "step_label": "Step",

    # -- categories --------------------------------------------------------
    "select_category": "Aap kya dhoond rahe hain?",
    "category_scholarship": "Scholarships",
    "category_job": "Naukriyan",
    "category_skills": "Hunar aur Training",
    "category_assistance": "Sarkari Imdaad",
    "category_unknown": "Deegar",
    "coming_soon": "Jald aa raha hai",
    "available_count": "{n} dastyab",
    "no_categories_selected": "Natayij dekhne ke liye upar se kam az kam ek category chunein.",
    "category_empty_note": "Is category mein abhi koi tasdeeq shuda record nahi, is liye yeh "
                           "band hai. Tafseel: PROJECT_TRACKER.md (DATA-03).",

    # -- profile -----------------------------------------------------------
    "profile_heading": "Apne baare mein thora bata dein",
    "profile_privacy_note": "Hum kabhi aapka naam, CNIC, phone number ya pata nahi poochte. "
                            "Yahan likhi koi cheez page band karne ke baad mehfooz nahi rehti.",
    "optional_hint": "Har khana optional hai — khali chhor dein to hum andaza lagane ke bajaye "
                     "use \"tasdeeq darkar\" likh dete hain.",
    "field_age": "Umar",
    "field_domicile": "Domicile suba",
    "field_education": "Sab se aala taleemi darja",
    "field_marks": "Aakhri imtihan ke marks (%)",
    "field_income": "Mahana ghar ki aamdani (PKR)",
    "field_enrolled": "Kya aap is waqt full-time student hain?",
    "field_existing_scholarship": "Kya pehle se koi aur scholarship mil rahi hai?",
    "field_employment": "Mulazmat ki soorat-e-haal",
    "field_experience": "Kaam ka tajurba (saal)",
    "placeholder_not_answered": "Batana nahi chahte",
    "option_yes": "Haan",
    "option_no": "Nahi",
    "option_employed": "Mulazmat par",
    "option_unemployed": "Be-rozgar",
    "edu_matric": "Matric",
    "edu_intermediate": "Intermediate",
    "edu_bachelor": "Bachelor",
    "edu_master": "Master",
    "see_matches": "Mere matches dikhayein",
    "update_matches": "Matches update karein",
    "reset_profile": "Saaf karein",
    "profile_completeness": "{total} mein se {answered} ke jawab diye",

    # -- results -----------------------------------------------------------
    "results_heading": "Aap ke natayij",
    "results_intro": "{n} record(s) ke against jaancha gaya. Yeh sirf maloomat ke liye hai — "
                     "apply karne se pehle official source se tasdeeq zaroor karein.",
    "status_eligible": "Ghalib gumaan hai ke aap eligible hain",
    "status_needs_verification": "Tasdeeq darkar",
    "status_not_eligible": "Filhaal match nahi karta",
    "listing_closed": "Darkhwastein band",
    "listing_closed_explainer": "Is listing ki aakhri tareekh guzar chuki hai. Yeh listing ke "
                                "baare mein hai, aap ke baare mein nahi — upar di gayi aap ki "
                                "eligibility waisi hi hai.",
    "group_eligible_help": "Jitni shartein hum jaanch sakte the, aap un sab par poore utarte hain.",
    "group_needs_verification_help": "Koi cheez aap ko rokti nahi — lekin kuch tafseelat abhi "
                                     "kam hain.",
    "group_not_eligible_help": "Kam az kam ek bayan karda shart aap ki maloomat se match nahi karti.",
    "no_results": "Muntakhab categories ke liye abhi koi mauqa load nahi hua.",
    "fill_profile_prompt": "Upar diya form bharein aur \"Mere matches dikhayein\" dabayein.",
    "missing_fields_hint": "{fields} ka jawab dein taake natija zyada wazeh ho jaye.",
    "why_match": "Yeh natija kyun?",
    "ai_explain_button": "Ise aasan alfaz mein samjhayein",
    "required_documents": "Zaroori dastavezat",
    "document_checklist_heading": "Dastavezat ki taiyari ki fehrist",
    "documents_ready": "{total} mein se {have} tayyar",
    "application_steps": "Darkhwast kaise dein",
    "official_source": "Official source",
    "open_official_site": "Official site kholein",
    "last_verified": "Aakhri tasdeeq",
    "provider_label": "Idara",
    "deadline_label": "Aakhri tareekh",
    "quota_note_label": "Khusoosi quota aur istisna",
    "ai_extracted_badge": "AI ne aap ki upload se parha — asal dastavez se milaan karein",
    "officially_verified_badge": "Sarkari taur par tasdeeq shuda",
    "unverified_badge": "Hamari team ne abhi tasdeeq nahi ki",
    "unverified_explainer": "Yeh record research se banaya gaya hai lekin team ne ise official "
                            "source se abhi confirm nahi kiya. Numbers ko ibtidayi samjhein, "
                            "aakhri nahi.",

    # -- upload / Lens -----------------------------------------------------
    "upload_ad_heading": "Ad, poster ya PDF upload karein",
    "upload_ad_intro": "Kisi bhi scholarship, job ya training ke ishtihar ki tasveer lein. "
                       "Sahulat AI use parhega, aap ko dikhayega ke usne kya paya, phir wahi "
                       "rules laga kar aap ki maloomat se jaanchega.",
    "upload_ad_button": "Yeh ad parhein",
    "upload_clear": "Yeh upload hata dein",
    "upload_privacy_note": "Aap ki file sirf isi request ke liye memory mein process hoti hai. "
                           "Na disk par mehfooz hoti hai, na kisi ke saath share hoti hai.",
    "extracted_fields_heading": "Hum ne aap ki file se kya parha",
    "extraction_confidence": "Parhne ka aetamaad",
    "confidence_high": "Ziyada",
    "confidence_medium": "Darmiyana",
    "confidence_low": "Kam",
    "screen_uploaded": "Ise meri maloomat se jaanchein",
    "upload_needs_profile": "Pehle \"Mauqe dhoondein\" tab par apni maloomat bharein — phir "
                            "wapas aayein aur hum yeh ad us se jaanch dein ge.",
    "raw_extraction_toggle": "Model ne bilkul kya wapas kiya, woh dekhein",
    "raw_extraction_note": "Ghair-tabdeel shuda JSON, taake aap upar di gayi har tafseel ko "
                           "asal dastavez se milaa sakein.",
    "stage_prepare": "Aap ki file tayyar ki ja rahi hai",
    "stage_read": "Dastavez ko AI se parha ja raha hai",
    "stage_structure": "Maloomat ko tarteeb diya ja raha hai",
    "stage_screen": "Aap ke jawabat se jaancha ja raha hai",
    # -- staged progress for the AI calls --
    "stage_ask_understand": "Aap ka sawal samjha ja raha hai",
    "stage_ask_search": "Hamare paas mojood indiraaj mein talaash jari hai",
    "stage_ask_gather": "Qareeb tareen indiraaj jama kiye ja rahe hain",
    "stage_ask_write": "Jawab likha ja raha hai, hawalon ke saath",
    "stage_explain_profile": "Aap ke jawabat parhe ja rahe hain",
    "stage_explain_decision": "Qawaid ke engine ka faisla parha ja raha hai",
    "stage_explain_write": "Ise aasan alfaaz mein bayan kiya ja raha hai",
    "stage_simplify_read": "Sarkari ibarat parhi ja rahi hai",
    "stage_simplify_write": "Ise aasan zaban mein dobara likha ja raha hai",
    "stage_running_note_ai": "Yeh amal Google ke servers par hota hai aur chand second leta hai. "
                             "Aap ka likha hua mehfooz nahi kiya jata, aur jawab sirf isi safhe par "
                             "dikhaye gaye indiraaj se ban sakta hai.",
    "stage_running_note_local": "Isi safhe ke indiraaj se kaam kiya ja raha hai. Koi AI key mojood "
                                "nahi, is liye neeche ki ibarat aarzi hai.",
    "stage_running_note": "Parhne ka amal Google ke servers par hota hai aur chand second leta "
                          "hai. Aap ki file mehfooz nahi ki jati.",
    "extracted_requirements": "Is dastavez mein bayan karda shartein",
    "extracted_nothing": "Is dastavez mein koi aisi shart nahi mili jo hum parh sakte.",
    "extracted_not_stated": "Is dastavez mein darj nahi",
    "extracted_not_stated_note": "In ke baare mein kuch nahi mila, is liye yeh aap par laagu "
                                 "nahi ki gayin. Is ka matlab eligibility nahi.",
    "extracted_documents": "Jo dastavezat maange gaye hain",
    "extracted_steps": "Darkhwast ka tareeqa, jaisa darj hai",
    "extracted_deadline": "Aakhri tareekh darj hai",
    "extracted_quota": "Tarjeeh darj hai",
    "extracted_category": "Kis qism ke taur par parha gaya",

    # -- scorecard ---------------------------------------------------------
    "scorecard_heading": "Eligibility ka tafseeli jaiza",
    "scorecard_summary": "{total} mein se {met} bayan karda shartein poori",
    "scorecard_summary_extra": "{unmet} poori nahi · {unknown} ki tasdeeq darkar",
    "scorecard_no_score_note": "Yeh neeche di gayi shartein ginne ka natija hai, kamyabi ke "
                               "imkan ka tanasub nahi. Faisla official rules karte hain, yeh "
                               "adad nahi.",
    "col_requirement": "Shart",
    "col_your_answer": "Aap ki maloomat",
    "col_result": "Natija",
    "result_passed": "Poori",
    "result_failed": "Poori nahi",
    "result_verify": "Tasdeeq darkar",

    # -- explanations ------------------------------------------------------
    "why_you_match": "Aap kyun eligible hain",
    "why_you_dont": "Aap filhaal kyun match nahi karte",
    "what_needs_verification": "Kis cheez ki tasdeeq darkar hai",
    "what_would_change": "Is mein kya farq daal sakta hai",
    "gap_line": "Is ke liye {required} darkar hai. Aap ki maloomat ke mutabiq {actual}.",
    "gap_unknown_line": "Is ke liye {required} darkar hai. Aap ne abhi is ka jawab nahi diya.",
    "what_would_change_caveat": "Sirf yeh shart poori karne se aap eligible sabit nahi ho jate "
                                "— baqi shartein bhi laagu hain, aur faisla metaaliqa idara hi "
                                "karta hai.",
    "decisive_note": "Ek shart poori na ho to natija badal jata hai, chahe baqi sab poori hon.",

    # -- top matches -------------------------------------------------------
    "top_matches_heading": "Aap ke liye behtareen mauqe",
    "top_matches_lede": "Tarteeb sirf haqaiq par hai — haisiyat, tasdeeq shuda shartein, aakhri "
                        "tareekh. Is tarteeb mein model ki raye shamil nahi.",
    "top_matches_empty": "Abhi koi mauqa is fehrist ke liye mozoon nahi. Aap ke mukammal "
                         "natayij neeche hain.",
    "rank_reason_all_met": "Tamam {total} shartein poori",
    "rank_reason_met": "{total} mein se {met} shartein poori",
    "rank_reason_priority": "aap {groups} tarjeehi zumre mein aate hain",
    "rank_reason_deadline": "{days} din mein band",
    "rank_reason_verify": "{unknown} ki tasdeeq baqi",

    # -- next action -------------------------------------------------------
    "next_step_label": "Agla qadam",
    "action_explore_others": "Apne doosre mozoon mauqe dekhein — yeh listing band ho chuki hai.",
    "action_review_blocker": "Darkhwast se pehle {subject} ki shart official source se dekh lein.",
    "action_answer_missing_one": "Ek aur sawal ka jawab dein taake ise jaancha ja sake — {subject}",
    "action_answer_missing_many": "{count} mazeed sawalat ke jawab dein taake yeh shartein "
                                  "jaanchi ja sakein.",
    "action_confirm_condition": "{subject} ki shart official source se tasdeeq karein.",
    "action_prepare_documents": "Is mauqe ke liye darkar {subject} dastavezat tayyar karein.",
    "action_apply": "Official source se darkhwast dein.",
    "action_check_source": "Maujuda tafseelat ke liye official source parhein.",
    "action_answer_now": "Abhi jawab dein",

    # -- architecture ------------------------------------------------------
    "architecture_heading": "Aap ki eligibility ka faisla AI nahi karta",
    "architecture_body": "Eligibility un shartoan se muqarrar hoti hai jo har idara shaya karta "
                         "hai, aur unhein tay-shuda rules jaanchte hain. Language model sirf "
                         "pehle se kiye gaye faisle ki wazahat karta hai, use badal nahi sakta.",
    "architecture_upload_label": "Upload ki gayi dastavez",
    "architecture_curated_label": "Hamara tayyar karda record",
    "architecture_same_engine": "Dono raste ek hi rules engine par khatam hote hain. Upload kiya "
                                "gaya ishtihar bilkul usi code se jaancha jata hai jo hamare "
                                "records ko jaanchta hai.",
    "pipeline_extract": "AI dastavez ko tarteeb-shuda khanon mein parhta hai",

    # -- landing -----------------------------------------------------------
    "home_paths_heading": "Apna rasta chunein",
    "path_scholarship": "Scholarship dhoondein",
    "path_job": "Naukri dhoondein",
    "path_skills": "Hunar seekhein",
    "path_assistance": "Madad dhoondein",
    "path_check_ad": "Ishtihar ki jaanch karein",
    "path_start": "Yahan se shuru karein",
    "hero_preview_alt": "Sahulat ke nataij ki jhalak: aik mauqa, janchi gayi sharait, aur agla qadam.",
    "hero_preview_note": "Yeh hamari fehrist se haqeeqi nataij hain, namoona profile par janche gaye - har zumre se aik, koi tasveeri namoona nahi.",
    "home_upload_hint": "Sahulat Lens kholta hai.",
    "path_check_ad_body": "Kahin koi poster, screenshot ya PDF mila? Use parhwa kar jaanch lein.",
    "benefits_heading": "Sahulat kyun",
    "benefit_personal_title": "Aap ke mutabiq",
    "benefit_personal_body": "Aap ki di gayi maloomat ke mutabiq, koi aam fehrist nahi.",
    "benefit_evidence_title": "Shawahid par mabni",
    "benefit_evidence_body": "Eligibility tay-shuda rules se nikalti hai, aur har record ka "
                             "source dikhaya jata hai.",
    "benefit_bilingual_title": "Do zubanon mein",
    "benefit_bilingual_body": "Poore safar mein English aur Urdu.",
    "benefit_realworld_title": "Asal ishtiharaat par kaam karta hai",
    "benefit_realworld_body": "Kahin se bhi mila poster ya PDF upload karein.",

    # -- correction --------------------------------------------------------
    "correct_heading": "Parhi gayi maloomat durust karein",
    "correct_note": "Tasveer se parhna hamesha durust nahi hota. Jo baat asal dastavez se match "
                    "na kare use theek karein, jaanch dobara ki jaye gi.",
    "correct_apply": "Durustagi laagu karein aur dobara jaanchein",
    "correct_applied": "Yeh jaanch aap ki durust karda maloomat par ki gayi hai, asal parhai par nahi.",
    "correct_deadline_hint": "Shakal: SAAL-MAHINA-DIN",
    "correct_none": "Darj nahi",

    # -- readiness ---------------------------------------------------------
    "readiness_heading": "Darkhwast ki taiyari",
    "readiness_percent": "{percent}% tayyar",
    "readiness_none": "Abhi kuch muntakhab nahi",
    "documents_you_have": "Jo dastavezat aap ke paas hain",
    "documents_still_needed": "Abhi darkar",
    "readiness_note": "Yeh sirf aap ki bhari hui fehrist dikhata hai. Yeh nahi jaanchta ke "
                      "dastavez durust, maujooda ya qabil-e-qubool hai — yeh sirf metaaliqa "
                      "daftar tay kar sakta hai.",
    "action_obtain_document": "Agli darkar dastavez hasil karein — {subject}",

    # -- deadlines ---------------------------------------------------------
    "urgency_passed": "Aakhri tareekh guzar chuki",
    "urgency_imminent": "Aakhri tareekh qareeb",
    "urgency_soon": "Jald darkhwast dein",
    "urgency_plenty": "Kaafi waqt baqi",
    "urgency_unknown": "Aakhri tareekh darj nahi",
    "days_remaining": "{days} din baqi",
    "days_remaining_one": "1 din baqi",
    "days_remaining_today": "Aaj aakhri din",
    "days_since_passed": "{days} din pehle band hua",
    "urgency_unknown_note": "Is record ke liye hamare paas koi aakhri tareekh nahi. Khula hone "
                            "ka andaza lagane se pehle official source dekhein.",
    "urgency_passed_note": "Darkhwastein band hain. Agla marhala khulne tak yahan kuch tayyar "
                           "karne ki zaroorat nahi.",

    # -- contextual Q&A ----------------------------------------------------
    "ask_about_this": "Is mauqe ke baare mein poochein",
    "ask_scoped_note": "Jawabat sirf isi record ke matan ko bator shawahid istemaal karte hain.",
    "chip_why_eligible": "Main kyun eligible hoon?",
    "chip_why_not_eligible": "Main kyun eligible nahi?",
    "chip_what_verify": "Kis cheez ki tasdeeq darkar hai?",
    "chip_this_deadline": "Aakhri tareekh kya hai?",
    "chip_where_apply": "Darkhwast kahan doon?",
    "chip_this_documents": "Kaun si dastavezat chahiye?",

    # -- passport ----------------------------------------------------------
    "passport_heading": "Mera opportunity passport",
    "passport_lede": "Ek baar jawab dein, har jagah istemaal karein. Yeh tafseelat har us mauqe "
                     "par laagu hoti hain jo aap kholte hain, upload kiye gaye ishtiharaat samet.",
    "passport_privacy": "CNIC, naam, phone number ya pata na manga jata hai na mehfooz kiya jata "
                        "hai. Aap ke jawabat sirf isi browser session mein rehte hain aur naye "
                        "sire se shuru karne par mit jate hain.",
    "passport_complete": "{percent}% mukammal",
    "passport_reuse": "Aap ke mehfooz jawabat istemaal ho rahe hain",

    # -- comparison --------------------------------------------------------
    "compare_heading": "Mauqon ka moazna",
    "compare_hint": "Moazne ke liye do ya zyada chunein.",
    "compare_factor": "Pehlu",
    "compare_eligibility": "Eligibility",
    "compare_conditions": "Poori shartein",
    "compare_deadline": "Aakhri tareekh",
    "compare_documents": "Darkar dastavezat",
    "compare_verification": "Zer-e-iltawa sawalat",
    "compare_apply": "Official link",
    "compare_easiest": "{name} ke liye nisbatan kam mehnat darkar hai: {reasons}.",
    "compare_reason_fewer_blockers": "kam ghair-poori shartein",
    "compare_reason_fewer_gaps": "kam zer-e-iltawa sawalat",
    "compare_reason_fewer_documents": "kam dastavezat jama karna baqi",
    "compare_effort_caveat": "Yeh mehnat ka moazna hai, faide ka nahi. Yeh nahi batata ke kaun "
                             "sa wazifa behtar hai ya milne ka imkan zyada hai.",
    "compare_too_close": "Dono taqreeban barabar mehnat talab hain. Faisla is bunyad par karein "
                         "ke pesh-kash kya hai.",

    # -- freshness ---------------------------------------------------------
    "freshness_heading": "Maloomat ki tazgi",
    "freshness_recent": "Haal hi mein tasdeeq shuda",
    "freshness_aging": "Tasdeeq ki sifarish",
    "freshness_stale": "Ghaliban purani",
    "freshness_never": "Hamari taraf se kabhi tasdeeq nahi",
    "freshness_days": "{days} din pehle jaancha gaya",
    "freshness_today": "Aaj jancha gaya",
    "freshness_yesterday": "Kal jancha gaya",
    "freshness_never_note": "Hamari team ne is record ki official source se tasdeeq nahi ki. "
                            "Fehrist mein hona maujooda hone ka saboot nahi.",
    "freshness_prompt": "In tafseelat par bharosa karne se pehle official page par tasdeeq karein.",

    # -- plain language ----------------------------------------------------
    "eli5_heading": "Aasan zubaan mein",
    "eli5_button": "Ise aasan alfaz mein samjhayein",
    "eli5_who_is_this_for": "Yeh kis ke liye hai?",
    "eli5_what_you_get": "Aap ko kya milta hai?",
    "eli5_who_can_apply": "Kaun darkhwast de sakta hai?",
    "eli5_what_you_need": "Aap ko kya darkar hai?",
    "eli5_where_to_apply": "Darkhwast kahan dein?",
    "eli5_caveat": "Yeh sirf isi record se AI ne aasan alfaz mein likha hai. Yeh koi shart barha "
                   "ya narm nahi kar sakta, aur eligibility ka faisla nahi karta — woh upar di "
                   "gayi shartein karti hain.",

    # -- source ------------------------------------------------------------
    "source_title_label": "Maakhaz dastavez",
    "source_org_label": "Idara",
    "source_url_label": "Official page",
    "source_none": "Koi official link darj nahi",

    # -- empty states ------------------------------------------------------
    "empty_try_heading": "Aap kya kar sakte hain",
    "empty_try_categories": "Koi aur category chunein",
    "empty_try_answers": "Apni taleemi sath ya domicile tabdeel karein",
    "empty_try_upload": "Kahin aur se mila ishtihar upload karein",
    "empty_catalogue_note": "Hamare paas filhaal {n} records hain. Fehrist ka mukhtasar hona is "
                            "prototype ki hadd hai, aap ke baare mein koi faisla nahi.",
    "documents_none_marked": "Aap ne abhi koi dastavez dastyab ke taur par nishan-zad nahi ki.",
    "documents_none_listed": "Is record mein darkar dastavezat darj nahi. Darkhwast se pehle "
                             "official page dekhein — yeh hamare record ki kami hai, is ka matlab "
                             "yeh nahi ke koi dastavez darkar nahi.",
    "answer_empty_hint": "Upar se koi sawal chunein taake isi record se jawab mil sake.",

    # -- degraded AI -------------------------------------------------------
    "ai_unavailable_heading": "AI tashreeh filhaal dastyab nahi",
    "ai_unavailable_body": "Is page par baqi sab kuch mutasir nahi hua: aap ka natija, jaanchi "
                           "gayi shartein, official source aur dastavezat ki fehrist — sab rules "
                           "se bante hain, AI se nahi.",
    "ai_offline_heading": "Bagair API key ke chal raha hai",
    "no_evidence_heading": "Is record se is ka jawab nahi diya ja sakta",
    "ai_retry": "Dobara koshish karein",

    # -- impact ------------------------------------------------------------
    "impact_heading": "Sahulat ka asar",
    "impact_screened": "mauqe jaanche gaye",
    "impact_requirements": "shartein jaanchi gayin",
    "impact_documents": "dastavezat ki nishandahi",
    "impact_minutes": "minute ki talash, takhmina",
    "impact_counted_note": "Sirf isi session se gina gaya. Kuch bhi users ke darmiyan muntaqil "
                           "ya mehfooz nahi hota.",
    "impact_estimate_note": "Waqt ka adad hi wahid takhmina hai: {n} mauqe × {minutes} minute "
                            "fi dasti talash. Yeh prototype ka takhmina hai, koi mapa gaya "
                            "dawa nahi.",
    "impact_estimate_badge": "Takhmina",

    # -- detail tabs -------------------------------------------------------
    "tab_eligibility": "Eligibility",
    "tab_documents": "Dastavezat aur marahil",
    "tab_source": "Maakhaz",
    "tab_ask": "Samjhein aur poochein",

    # -- provisional deadlines --------------------------------------------
    "deadline_provisional_badge": "Aarzi tareekh",

    # -- always-open enrolment --------------------------------------------
    "listing_always_open": "Hamesha khula",
    "urgency_continuous": "Koi aakhri tareekh nahi",
    "urgency_continuous_note": "Yeh program saara saal darkhwastein qabool karta hai. Koi aakhri "
                               "tareekh nahi jo nikal jaye - lekin manzoori ka inhesaar upar di "
                               "gayi sharait aur darkhwast ke waqt funds ki dastyabi par hai.",
    "deadline_provisional_note": "Yeh tareekh mutawaqqa marhale ke liye hamari aarzi tareekh hai, "
                                 "idare ki elan karda nahi. Ginti ko andaza samjhein aur official "
                                 "page par tasdeeq karein.",

    # -- follow-up ---------------------------------------------------------
    "ask_followup": "Koi aur sawal poochein",
    "ask_followup_hint": "Jawabat sirf upar diye records se aate hain aur hamesha source batate hain.",
    "ask_placeholder": "misaal: PEEF scholarship ke liye kaun si dastavezat chahiye?",
    "ask_button": "Poochein",
    "no_evidence_found": "Hamare records mein is baare mein tasdeeq shuda maloomat nahi. Baraye "
                         "meherbani metaaliqa program ka official link dekhein.",
    "ai_enabled": "AI khususiyat faal",
    "ai_mock_mode": "Offline mode — koi API key nahi",
    "ai_mock_explainer": "Eligibility ki jaanch bagair API key ke poori kaam karti hai kyunke "
                         "yeh rules par mabni hai. Sirf aasan tashreeh aur ad parhne ke liye "
                         "key darkar hai.",
    "ai_unavailable": "AI tashreeh is waqt dastyab nahi. Upar diya natija rules par mabni hai "
                      "aur us par koi asar nahi para.",
    "ai_mock_notice": "Offline mode — yahan aasan tashreeh ke liye Gemini key shamil karein.",
    "ai_mock_extraction_notice": "Offline mode — asal ad parhne ke liye Gemini key darkar hai.",

    # -- status panel ------------------------------------------------------
    "sidebar_language": "Zubaan",
    "sidebar_status": "Haisiyat",
    "sidebar_catalog": "Fehrist",
    "sidebar_records": "{n} records load huye",
    "sidebar_verified": "{n} tasdeeq shuda",
    "sidebar_unverified": "{n} tasdeeq ke muntazir",
    "sidebar_about": "Taaruf",
    "sidebar_about_body": "Sahulat AI aap ki maloomat ko Pakistani sarkari programon ke against "
                          "ek tay-shuda rules engine se jaanchta hai. AI sirf natayij samjhane "
                          "aur upload kiye gaye ishtiharaat parhne ke liye hai — eligibility ka "
                          "faisla kabhi nahi karta.",
    "search_mode": "Talash ka tareeqa",
    "search_mode_semantic": "Maani ke mutabiq",
    "search_mode_keyword": "Lafz ke mutabiq",

    # -- how it works ------------------------------------------------------
    "how_heading": "Sahulat AI kaise kaam karta hai",
    "how_intro": "Zyadatar AI tools mein language model tay karta hai ke kaun eligible hai. Hum "
                 "aisa nahi karte. Eligibility ek tay-shuda rules engine tay karta hai jise aap "
                 "parh aur jaanch sakte hain. AI sirf wazahat karta hai.",
    "how_step1_title": "1. Aap apne baare mein batate hain",
    "how_step1_body": "Sirf jaanch ke liye zaroori tafseelat — umar, domicile, taleem, marks, "
                      "aamdani. Naam, CNIC, phone ya pata kabhi nahi.",
    "how_step2_title": "2. Rules faisla karte hain",
    "how_step2_body": "Har shart alag alag shaya-shuda mayaar se jaanchi jati hai aur poori, "
                      "poori nahi, ya na-maloom likhi jati hai. Kami ka andaza kabhi nahi lagaya jata.",
    "how_step3_title": "3. AI wazahat karta hai",
    "how_step3_body": "Language model ko faisla diya jata hai aur woh use aasan alfaz mein rakhta "
                      "hai. Woh natija badal nahi sakta, na koi nayi shart bana sakta hai.",
    "how_trust_heading": "Hum bharose ko kaise sambhalte hain",
    "how_trust_body": "Official sources se tayyar karda records aur aap ki uploads se parhe gaye "
                      "records kabhi mix nahi hote. Har ek ka apna badge hai, aur upload kiya "
                      "gaya record hamesha yeh batata hai.",
    "how_privacy_heading": "Hum kya kabhi jama nahi karte",

    # -- wizard ------------------------------------------------------------
    "step_focus_title": "Aap kya dhoond rahe hain?",
    "step_focus_caption": "Ek ya zyada categories chunein. Hum sirf inhi ke against jaanchein ge.",
    "step_about_title": "Aap ke baare mein",
    "step_about_caption": "Bunyadi tafseelat jin par taqreeban har program jaanch karta hai.",
    "step_education_title": "Taleem",
    "step_education_caption": "Aap ka mukammal karda sab se aala darja, aur karkardagi.",
    "step_circumstances_title": "Hunar aur halaat",
    "step_circumstances_caption": "Optional, lekin har jawab aap ke natayij ko wazeh karta hai "
                                  "aur aise program khol sakta hai jin mein makhsoos nashistein hain.",
    "step_results_title": "Aap ke natayij",
    "step_results_caption": "Un tamam programon ke against jaancha gaya jo aap ne chune.",
    "nav_back": "Wapas",
    "nav_continue": "Aage barhein",
    "nav_see_results": "Mere natayij dekhein",
    "nav_start_over": "Naye sire se shuru karein",
    "nav_edit_answers": "Apne jawabat tabdeel karein",
    "step_counter": "Step {current} / {total}",
    "required_marker": "Zaroori",
    "optional_marker": "Optional",
    "fix_before_continuing": "Aage barhne se pehle nishan-zad khane mukammal karein.",
    "your_answers": "Aap ke jawabat",
    "detail_completeness": "{percent}% optional tafseel di gayi",
    "more_detail_hint": "Mazeed sawalat ke jawab dene se \"Tasdeeq darkar\" natayij wazeh ho jate hain.",

    # -- validation --------------------------------------------------------
    "err_required": "Aap ko jaanchne ke liye yeh jawab zaroori hai.",
    "err_age_range": "{min} aur {max} ke darmiyan umar likhein.",
    "err_marks_range": "Marks 0 aur 100 ke darmiyan hone chahiye.",
    "err_income_range": "Mahana raqam rupay mein likhein.",
    "err_experience_range": "0 se 50 saal ke darmiyan likhein.",
    "err_no_category": "Kam az kam ek category chunein.",
    "err_invalid_choice": "Di gayi options mein se ek chunein.",

    # -- extra profile fields ---------------------------------------------
    "field_gender": "Jins",
    "field_gender_help": "Sirf is liye poocha jata hai ke kuch program khawateen ke liye "
                         "nashistein makhsoos rakhte hain.",
    "gender_female": "Khatoon",
    "gender_male": "Mard",
    "gender_other": "Khud bayan karna chahte hain",
    "field_field_of_study": "Taleemi shoba",
    "fos_engineering": "Engineering",
    "fos_computer_science": "Computer Science / IT",
    "fos_medical": "Medical aur Sehat",
    "fos_natural_sciences": "Natural Sciences",
    "fos_social_sciences": "Social Sciences",
    "fos_business": "Business aur Commerce",
    "fos_arts_humanities": "Arts aur Humanities",
    "fos_education": "Taleem",
    "fos_agriculture": "Zaraat",
    "fos_law": "Qanoon",
    "fos_other": "Deegar",
    "field_english_level": "English ki mahaarat",
    "eng_none": "Bilkul nahi",
    "eng_basic": "Bunyadi — saday alfaz aur jumlay",
    "eng_intermediate": "Darmiyana — baat cheet kar sakte hain",
    "eng_fluent": "Rawaan — parhna likhna aasan hai",
    "field_computer_skills": "Computer aur digital hunar",
    "comp_none": "Bilkul nahi",
    "comp_basic": "Bunyadi — email, browsing, typing",
    "comp_intermediate": "Darmiyana — office software, spreadsheets",
    "comp_advanced": "Aala — programming, design, data",
    "field_has_disability": "Kya aap kisi maazoori ka shikar hain?",
    "field_is_orphan": "Kya aap yateem hain?",
    "special_circumstances": "Khusoosi halaat",
    "special_circumstances_help": "Kai program in zumron ke liye nashistein makhsoos rakhte hain. "
                                  "Jawab dena sirf aap ke faide mein hai — ise kabhi kisi ko "
                                  "bahar karne ke liye istemaal nahi kiya jata.",
    "priority_heading": "Aap makhsoos nashist ke liye mozoon ho sakte hain",
    "priority_body": "Yeh program in ko tarjeeh deta hai: {groups}. Maujooda quota rules official "
                     "source se confirm karein.",
    "pg_female": "khawateen darkhwast dahindgan",
    "pg_disability": "maazoori ke haamil darkhwast dahindgan",
    "pg_orphan": "yateem darkhwast dahindgan",
    "pg_minority": "mazhabi aqliyatein",
    "pg_under_served_district": "pas-manda azila",

    # -- brand / hero ------------------------------------------------------
    "brand_urdu": "Sahulat",
    "nav_discover": "Daryaft karein",
    "nav_read": "Ishtihar parhwayein",
    "nav_how": "Yeh kaise kaam karta hai",
    "hero_eyebrow": "Pakistan ka Opportunity Navigator",
    "hero_title": "Aise mauqe dhoondein jo aap ki zindagi se mail khayein.",
    "hero_body": "Scholarships, naukriyan, training aur muntakhab sarkari program — wazeh "
                 "eligibility rules se match kiye gaye aur official sources se samjhaye gaye.",
    "cta_start": "Apne baare mein batayein",
    "cta_sample": "Namoona profile azmayein",
    "trust_rules": "Rules par mabni matching",
    "trust_sources": "Official source ke shawahid",
    "trust_no_pii": "Koi hassas shanakht nahi",
    "map_you": "Aap",
    "find_heading": "Sahulat AI aap ko kya dhoondne mein madad de sakta hai?",
    "find_scholarship": "Talaba ke liye maali madad.",
    "find_job": "Sarkari aur public-sector naukriyan.",
    "find_skills": "Hunar aur peshawarana tarraqi.",
    "find_assistance": "Awami imdaad ke program.",

    # -- journey / principles ---------------------------------------------
    "journey_heading": "Maloomat se mauqe tak",
    "journey_line": "Aap batayein. Rules jaanchein. Sources samjhayein. Faisla aap ka.",
    "journey_1_title": "Apne baare mein batayein",
    "journey_1_body": "Sirf wohi tafseelat jo matching ke liye zaroori hain.",
    "journey_2_title": "Rules mayaar jaanchte hain",
    "journey_2_body": "Koi andaza nahi. Kami wali maloomat na-maloom hi rehti hai.",
    "journey_3_title": "Sources shawahid dete hain",
    "journey_3_body": "Hum batate hain ke ahem baatein kahan se aayi hain.",
    "journey_4_title": "Aap ko agla qadam milta hai",
    "journey_4_body": "Dastavezat, haisiyat aur official darkhwast ka link.",
    "principles_heading": "Teen usoolon par bana hua",
    "principle_1_title": "Rules faisla karte hain",
    "principle_1_body": "Eligibility tarteeb-shuda mayaar se jaanchi jati hai, language model "
                        "ke andaze se nahi.",
    "principle_2_title": "Sources sahara dete hain",
    "principle_2_body": "Ahem baatein un shaya-shuda sources se judi hoti hain jahan se woh aayi hain.",
    "principle_3_title": "AI wazahat karta hai",
    "principle_3_body": "Model tay-shuda natije ko qabil-e-faham rehnumai mein badalta hai — "
                        "natija badal nahi sakta.",
    "privacy_heading": "Aap ki niji maloomat",
    "privacy_body": "Sahulat AI ko mauqe batane ke liye aap ka CNIC, naam, phone number ya pata "
                    "darkar nahi. Page band karne ke baad aap ki likhi koi cheez mehfooz nahi rehti.",

    # -- source / listing --------------------------------------------------
    "source_heading": "Maakhaz",
    "source_verified": "Maakhaz tasdeeq shuda",
    "source_needs_check": "Maujooda marhale ki tasdeeq karein",
    "source_last_checked": "Aakhri baar jaancha",
    "source_not_checked": "Hamari team ne abhi nahi jaancha",
    "source_verify_body": "Eligibility ki maloomat shaya shuda hai, lekin maujooda darkhwast ka "
                          "marhala tabdeel ho sakta hai. Apply karne se pehle official page par "
                          "tasdeeq karein.",
    "listing_open": "Khula hai",
    "listing_verify_cycle": "Maujooda marhale ki tasdeeq karein",
    "match_likely": "Ghalib gumaan hai ke match karta hai",
    "match_needs_verification": "Tasdeeq darkar",
    "match_none": "Filhaal match nahi karta",

    # -- results chrome ----------------------------------------------------
    "results_found": "Hum ne {n} mauqe dhoonde jo dekhne laiq hain",
    "results_found_one": "Hum ne 1 mauqa dhoonda jo dekhne laiq hai",
    "results_breakdown": "{strong} mazboot · {verify} tasdeeq darkar · {no} match nahi",
    "first_card_note": "Yeh khaas taur par aap ke liye mozoon lagta hai.",
    "why_matches_you": "Yeh aap se kyun match karta hai",
    "view_eligibility": "Eligibility dekhein",
    "how_generated": "Yeh natija kaise bana",
    "pipeline_profile": "Aap ki maloomat",
    "pipeline_rules": "Eligibility rules",
    "pipeline_match": "Tarteeb-shuda match",
    "pipeline_retrieval": "Official source se maloomat",
    "pipeline_explain": "AI ki wazahat",
    "timeline_heading": "Darkhwast ka safar",
    "empty_heading": "Abhi koi mazboot match nahi mila.",
    "empty_body": "Apni taleemi sath, chuni gayi categories ya domicile tabdeel kar ke dekhein.",
    "error_busy": "Sahulat AI is waqt masroof hai. Aap ki maloomat mehfooz hai — thori der baad "
                  "dobara koshish karein.",
    "technical_details": "Tikneeki tafseelat",
    "demo_badge": "Namoona profile",
    "demo_note": "Aap ek namoona profile dekh rahe hain. Apni maloomat dalne ke liye naye sire "
                 "se shuru karein.",
    "chip_what_apply": "Main kis cheez ke liye apply kar sakta hoon?",
    "chip_why_qualify": "Main kyun eligible hoon?",
    "chip_documents": "Mujhe kaun si dastavezat chahiye?",

    # -- footer / stats ----------------------------------------------------
    "footer_tagline": "Mauqon tak rasai, aasan tareeqe se.",
    "footer_trust": "Bharosa",
    "footer_language": "Zubaan",
    "language_help": "Poore safhe ki zaban tabdeel karein.",
    "footer_built": "Pakistan ke liye banaya gaya",
    "footer_disclaimer": "Sirf maloomati rehnumai. Sahulat AI koi sarkari eligibility faisla nahi "
                         "karta, shanakht ki tasdeeq nahi karta, aur aap ki taraf se darkhwast "
                         "jama nahi karta.",
    "catalogue_stat": "tayyar karda mauqe",
    "authorities_stat": "sarkari idare",
    "sourced_stat": "source se judey records",
    "identifiers_stat": "hassas shanakht darkar",
    "export_heading": "Apne natayij mehfooz karein",
    "export_button": "Khulasa download karein (.txt)",
    "export_hint": "Aap ke matches, dastavezat aur agle qadmon ki saada text naqal.",
}
