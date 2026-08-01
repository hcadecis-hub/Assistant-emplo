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
    """Extrait le texte d'un fichier PDF uplaodé."""
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
    Tu es un expert en recrutement. Ton but est de rédiger une lettre de motivation percutante, 
    structurée et professionnelle.
    Règles strictes :
    - Va droit au but, adopte un ton analytique et orienté résultats.
    - Fais le lien EXPLICITE entre les compétences demandées dans l'offre et les expériences du candidat.
    - Ne mens pas et n'invente pas d'expériences que le candidat n'a pas.
    - Évite le jargon creux et les formules de politesse interminables.
    """
    
    prompt_utilisateur = f"""
    Rédige une lettre de motivation pour le poste de '{poste}' chez '{entreprise}'.
    Voici le profil et les expériences du candidat (CV) :
    {cv_texte}
    Voici la description de l'offre d'emploi :
    {description_offre}
    """

    try:
        reponse = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt_systeme},
                {"role": "user", "content": prompt_utilisateur}
            ],
            temperature=0.7
        )
        return reponse.choices[0].message.content
    except Exception as e:
        return f"Erreur : {str(e)}"

# --- INTERFACE GRAPHIQUE ---

st.title("🚀 Mon Assistant de Candidature")

# Barre latérale (Sidebar) pour les paramètres et le CV
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Clé API OpenAI", type="password", help="Ta clé ne sera pas sauvegardée.")
    
    st.markdown("---")
    
    st.header("📄 Mon Profil (PDF)")
    fichier_cv = st.file_uploader("Uploade ton CV au format PDF", type=["pdf"])
    
    st.markdown("---")
    st.write("Cet outil génère des lettres sur-mesure basées sur TES expériences.")

# Zone principale avec des onglets
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
                with st.spinner("Lecture du PDF et rédaction en cours..."):
                    # 1. Extraction du texte du PDF
                    cv_texte = extraire_texte_pdf(fichier_cv)
                    
                    # 2. Génération de la lettre
                    lettre = generer_lettre(api_key, entreprise, poste, description, cv_texte)
                    st.text_area("Lettre générée :", value=lettre, height=400)
                    
                    # 3. Mise à jour de l'Excel en arrière-plan
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
        st.info("Aucune candidature enregistrée pour le moment. Le fichier sera créé lors de la première génération.")
