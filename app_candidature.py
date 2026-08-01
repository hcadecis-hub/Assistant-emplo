import streamlit as st
import pandas as pd
import os
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
        return f"Erreur lors de la lecture du PDF : {str(e)}"

def generer_lettre(api_key, entreprise, poste, description_offre, cv_texte):
    client = OpenAI(api_key=api_key)
    
    prompt_systeme = """
    Tu es un expert en recrutement. Ton rôle est de rédiger une lettre de motivation pour le candidat, mais avec une contrainte absolue : 
    Tu DOIS te calquer fidèlement sur le modèle de lettre fourni par l'utilisateur. 
    
    Règles strictes :
    1. Conserve la structure exacte, la tonalité analytique et humble, ainsi que les éléments biographiques du modèle (Master en Économie du droit, mémoire sur l'ATT d'Apple, Python, R, Power BI).
    2. Adapte le premier paragraphe pour insérer le nom du poste et de l'entreprise cible.
    3. Ajoute 1 ou 2 phrases subtiles dans le texte pour faire le lien entre les compétences du candidat et les besoins spécifiques de l'offre d'emploi.
    4. Garde la conclusion et la signature 'Francis MBUNGU' telles quelles. Ne rajoute pas de fioritures.
    """
    
    lettre_modele = """
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
    
    prompt_utilisateur = f"""
    Voici l'offre d'emploi cible :
    - Entreprise : {entreprise}
    - Poste : {poste}
    - Description de l'offre : {description_offre}
    
    Voici le CV du candidat (pour piocher un détail pertinent si nécessaire) :
    {cv_texte}
    
    Voici LE MODÈLE DE LETTRE à utiliser et à adapter subtilement à l'offre :
    {lettre_modele}
    """

    try:
        reponse = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt_systeme},
                {"role": "user", "content": prompt_utilisateur}
            ],
            temperature=0.4 # Une température plus basse (0.4) force l'IA à rester très proche du modèle
        )
        return reponse.choices[0].message.content
    except Exception as e:
        return f"Erreur : {str(e)}"

# --- INTERFACE GRAPHIQUE ---

st.title("🚀 Mon Assistant de Candidature")

with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Clé API OpenAI", type="password", help="Ta clé ne sera pas sauvegardée.")
    st.markdown("---")
    st.header("📄 Mon Profil (PDF)")
    fichier_cv = st.file_uploader("Uploade ton CV au format PDF", type=["pdf"])
    st.markdown("---")
    st.write("L'IA utilise désormais ton modèle de lettre strict (Master Éco du droit, ATT Apple...) et l'adapte à l'offre.")

onglet_generation, onglet_suivi = st.tabs(["✍️ Nouvelle Candidature", "📊 Mon Suivi (Excel)"])

with onglet_generation:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Détails de l'offre")
        entreprise = st.text_input("🏢 Nom de l'entreprise")
        poste = st.text_input("🎯 Titre du poste")
        lien = st.text_input("🔗 Lien vers l'offre")
        description = st.text_area("📋 Description complète de l'annonce", height=200)
        
        bouton_generer = st.button("✨ Générer la lettre et sauvegarder", type="primary")

    with col2:
        st.subheader("Résultat")
        if bouton_generer:
            if not api_key:
                st.error("⚠️ Tu dois renseigner ta clé API dans le menu à gauche.")
            elif fichier_cv is None:
                st.warning("⚠️ N'oublie pas d'uploader ton CV (PDF) dans le menu à gauche.")
            elif not entreprise or not poste or not description:
                st.warning("⚠️ Remplis au moins l'entreprise, le poste et la description de l'offre.")
            else:
                with st.spinner("Lecture du PDF et adaptation de ta lettre en cours..."):
                    cv_texte = extraire_texte_pdf(fichier_cv)
                    lettre = generer_lettre(api_key, entreprise, poste, description, cv_texte)
                    st.text_area("Lettre générée :", value=lettre, height=400)
                    mettre_a_jour_tracker(entreprise, poste, lien)
                    st.success("✅ Candidature ajoutée au fichier de suivi !")

with onglet_suivi:
    st.subheader("Historique des candidatures")
    if os.path.exists(FICHIER_EXCEL):
        df_suivi = pd.read_excel(FICHIER_EXCEL)
        st.dataframe(df_suivi, use_container_width=True)
        
        with open(FICHIER_EXCEL, "rb") as f:
            st.download_button(
                label="📥 Télécharger le fichier Excel",
                data=f,
                file_name=FICHIER_EXCEL,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("Aucune candidature enregistrée pour le moment.")
