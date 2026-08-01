import streamlit as st
import pandas as pd
import os
import json
import requests
from datetime import datetime
from openai import OpenAI
import PyPDF2

# --- CONFIGURATION ---
FICHIER_EXCEL = "suivi_candidatures.xlsx"

st.set_page_config(page_title="Assistant de Candidature", page_icon="💼", layout="wide")

def mettre_a_jour_tracker(entreprise, poste, lien):
    nouvelle_candidature = {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Entreprise": entreprise,
        "Poste": poste,
        "Lien": lien,
        "Statut": "Candidature préparée",
        "Relance prévue le": ""
    }
    if not os.path.exists(FICHIER_EXCEL):
        df = pd.DataFrame([nouvelle_candidature])
    else:
        df = pd.read_excel(FICHIER_EXCEL)
        df = pd.concat([df, pd.DataFrame([nouvelle_candidature])], ignore_index=True)
    df.to_excel(FICHIER_EXCEL, index=False)
    return df

def extraire_texte_pdf(fichier_pdf):
    try:
        lecteur = PyPDF2.PdfReader(fichier_pdf)
        texte = ""
        for page in lecteur.pages:
            texte += page.extract_text() + "\n"
        return texte
    except Exception as e:
        return f"Erreur de lecture PDF : {str(e)}"

# Ton modèle de lettre strict
LETTRE_MODELE = """
Madame, Monsieur,

Titulaire d'un Master en Économie du droit, je souhaite vous adresser ma candidature au poste de [intitulé du poste].

Au fil de mon parcours, je me suis progressivement orienté vers les questions de régulation, de conformité et d'analyse économique. Ce qui m'intéresse avant tout n'est pas uniquement la technicité de ces domaines, mais leur finalité : comprendre le fonctionnement des organisations, identifier les risques, produire une analyse utile et contribuer à des décisions plus solides. C'est cette manière d'aborder les sujets qui me conduit aujourd'hui à candidater auprès de votre structure.

Mon mémoire de recherche, consacré aux effets de l'App Tracking Transparency d'Apple sur la concurrence et la régulation des marchés numériques, illustre cette démarche. Au-delà de l'étude d'un cas particulier, ce travail m'a amené à analyser les conséquences économiques d'une décision réglementaire, à croiser différentes approches et à construire un raisonnement rigoureux sur des problématiques complexes.

J'apprécie particulièrement les missions qui demandent d'aller au-delà des apparences : comprendre un processus, analyser des données, évaluer un risque ou produire une synthèse claire à partir d'informations parfois dispersées. Je maîtrise les outils d'analyse tels que Python, R et Power BI, mais je considère surtout qu'un bon analyste est d'abord quelqu'un qui sait poser les bonnes questions, structurer son raisonnement et conserver un regard critique sur ses propres conclusions.

Je suis également à l'aise dans le travail collectif. J'apprécie les environnements où les compétences se complètent, où les analyses se confrontent et où chacun contribue à une réflexion commune. Ma maîtrise de l'anglais me permet par ailleurs d'évoluer dans un contexte international et de travailler sur des documents ou des échanges professionnels en langue anglaise.

Si je souhaite rejoindre votre équipe, c'est parce que je pense pouvoir y apporter ma capacité d'analyse, ma curiosité intellectuelle et mon envie d'apprendre, tout en continuant à développer mes compétences auprès de professionnels exigeants.

Je vous remercie de l'attention portée à ma candidature et me tiens à votre disposition pour un entretien.

Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

Francis MBUNGU
"""

def generer_lettre_auto(api_key, url, cv_texte):
    try:
        reponse_web = requests.get(f"https://r.jina.ai/{url}")
        texte_page = reponse_web.text
    except Exception as e:
        return None, f"Impossible de lire le lien : {str(e)}"

    client = OpenAI(api_key=api_key)
    
    prompt_systeme = """
    Tu es un assistant de recrutement automatisé. Tu reçois la page web d'une offre d'emploi, et le CV d'un candidat.
    
    Ta mission STRICTE :
    1. Extraire le nom de l'entreprise qui recrute UNIQUEMENT à partir de la section "PAGE WEB".
    2. Extraire le titre du poste UNIQUEMENT à partir de la section "PAGE WEB".
    3. Rédiger la lettre de motivation en adaptant le modèle fourni.
    
    ⚠️ RÈGLE ANTI-HALLUCINATION : Ne confonds JAMAIS les expériences du candidat (dans la section CV) avec l'offre cible. 
    Si la section "PAGE WEB" ne contient pas d'offre d'emploi claire (message d'erreur, captcha, page vide), mets la valeur "ERREUR" pour les clés "entreprise" et "poste".
    
    Réponds obligatoirement en format JSON avec ces 3 clés : "entreprise", "poste", "lettre".
    """
    
    prompt_utilisateur = f"""
    --- DÉBUT DE LA PAGE WEB (OFFRE CIBLE) ---
    {texte_page}
    --- FIN DE LA PAGE WEB ---
    
    --- DÉBUT DU CV DU CANDIDAT (SON PASSÉ) ---
    {cv_texte}
    --- FIN DU CV ---
    
    --- MODÈLE DE LETTRE À UTILISER ---
    {LETTRE_MODELE}
    """

    try:
        reponse = client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": prompt_systeme}, 
                {"role": "user", "content": prompt_utilisateur}
            ],
            temperature=0.1
        )
        
        donnees = json.loads(reponse.choices[0].message.content)
        
        if donnees.get("entreprise") == "ERREUR" or donnees.get("poste") == "ERREUR":
            return None, "❌ Impossible de lire l'offre sur ce site web (blocage anti-robot). Utilise l'onglet 'Mode Manuel'."
            
        return donnees, None
        
    except Exception as e:
        return None, f"Erreur d'analyse IA : {str(e)}"


def generer_lettre_depuis_texte(api_key, texte_brut, cv_texte, lien):
    client = OpenAI(api_key=api_key)
    prompt_systeme = """
    Tu es un assistant de recrutement. L'utilisateur a copié-collé l'intégralité d'une page web d'offre d'emploi (ce texte peut être très brouillon et contenir des menus ou des pubs).
    
    Ta mission :
    1. Trouver le nom de l'entreprise.
    2. Trouver le titre du poste.
    3. Rédiger la lettre en adaptant STRICTEMENT le modèle fourni.
    
    Réponds OBLIGATOIREMENT en JSON avec les clés : "entreprise", "poste", "lettre".
    """
    
    prompt_utilisateur = f"TEXTE DE L'OFFRE :\n{texte_brut}\n\nCV :\n{cv_texte}\n\nMODELE :\n{LETTRE_MODELE}"

    try:
        reponse = client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_format={ "type": "json_object" },
            messages=[{"role": "system", "content": prompt_systeme}, {"role": "user", "content": prompt_utilisateur}],
            temperature=0.1
        )
        return json.loads(reponse.choices[0].message.content), None
    except Exception as e:
        return None, f"Erreur IA : {str(e)}"


# --- INTERFACE GRAPHIQUE ---
st.title("🚀 Mon Assistant de Candidature")

with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Clé API OpenAI", type="password")
    st.markdown("---")
    st.header("📄 Mon Profil (PDF)")
    fichier_cv = st.file_uploader("Uploade ton CV", type=["pdf"])

onglet_generation, onglet_suivi = st.tabs(["✍️ Nouvelle Candidature", "📊 Mon Suivi (Excel)"])

with onglet_generation:
    tab_auto, tab_manuel = st.tabs(["✨ Mode Magique (Lien)", "✍️ Mode Manuel (Copier-Coller)"])
    
    with tab_auto:
        st.write("Colle simplement le lien de l'offre (WttJ, Indeed...). L'IA s'occupe de tout lire.")
        lien_auto = st.text_input("🔗 Lien URL de l'offre")
        btn_auto = st.button("🚀 Extraire et Générer", type="primary", key="btn_auto")
        
        if btn_auto:
            if not api_key or fichier_cv is None or not lien_auto:
                st.warning("⚠️ Vérifie que ta clé API, ton CV et le lien sont bien renseignés.")
            else:
                with st.spinner("Lecture du lien, extraction des données et rédaction en cours..."):
                    cv_texte = extraire_texte_pdf(fichier_cv)
                    resultats, erreur = generer_lettre_auto(api_key, lien_auto, cv_texte)
                    
                    if erreur:
                        st.error(erreur)
                    else:
                        st.success(f"✅ Offre détectée : {resultats['poste']} chez {resultats['entreprise']}")
                        st.text_area("Lettre générée :", value=resultats['lettre'], height=400, key="lettre_auto")
                        mettre_a_jour_tracker(resultats['entreprise'], resultats['poste'], lien_auto)
                        st.success("✅ Candidature ajoutée au fichier de suivi !")
                        
    with tab_manuel:
        st.write("Anti-robot bloquant ? Fais `Ctrl+A` puis `Ctrl+C` sur la page de l'offre et colle TOUT ici. L'IA fera le tri.")
        lien_manuel = st.text_input("🔗 Lien vers l'offre (pour ton fichier de suivi Excel)")
        texte_brut = st.text_area("📋 Colle TOUT le texte de la page ici (même avec les menus)", height=200)
        btn_manuel = st.button("✨ Analyser le texte et Générer", type="primary", key="btn_manuel")
        
        if btn_manuel:
            if not api_key or fichier_cv is None or not texte_brut:
                st.warning("⚠️ Remplis la zone de texte, uploade ton CV et mets ta clé API.")
            else:
                with st.spinner("Analyse du texte brouillon en cours..."):
                    cv_texte = extraire_texte_pdf(fichier_cv)
                    resultats, erreur = generer_lettre_depuis_texte(api_key, texte_brut, cv_texte, lien_manuel)
                    
                    if erreur:
                        st.error(erreur)
                    else:
                        st.success(f"✅ Offre détectée dans le texte : {resultats['poste']} chez {resultats['entreprise']}")
                        st.text_area("Lettre générée :", value=resultats['lettre'], height=400, key="lettre_texte")
                        mettre_a_jour_tracker(resultats['entreprise'], resultats['poste'], lien_manuel)
                        st.success("✅ Candidature ajoutée au fichier de suivi !")

with onglet_suivi:
    st.subheader("Historique des candidatures")
    if os.path.exists(FICHIER_EXCEL):
        df_suivi = pd.read_excel(FICHIER_EXCEL)
        st.dataframe(df_suivi, use_container_width=True)
        with open(FICHIER_EXCEL, "rb") as f:
            st.download_button(label="📥 Télécharger le fichier Excel", data=f, file_name=FICHIER_EXCEL, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Aucune candidature enregistrée pour le moment.")
