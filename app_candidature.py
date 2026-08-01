import streamlit as st
import pandas as pd
import os
from datetime import datetime
from openai import OpenAI

# --- CONFIGURATION ---
FICHIER_EXCEL = "suivi_candidatures.xlsx"

# Paramétrage de la page Web
st.set_page_config(page_title="Assistant de Candidature", page_icon="💼", layout="wide")

def mettre_a_jour_tracker(entreprise, poste, lien):
    """Met à jour le fichier Excel et retourne le DataFrame."""
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

def generer_lettre(api_key, entreprise, poste, description_offre):
    """Génère la lettre via OpenAI."""
    client = OpenAI(api_key=api_key)
    
    prompt_systeme = """
    Tu es un expert en recrutement. Ton but est de rédiger une lettre de motivation percutante, 
    structurée et professionnelle pour un candidat postulant dans le domaine de l'économie, de l'analyse ou du conseil.
    Règles strictes :
    - Va droit au but, adopte un ton analytique et orienté résultats.
    - Évite le jargon creux et les formules de politesse interminables.
    """
    
    prompt_utilisateur = f"Rédige une lettre de motivation pour le poste de '{poste}' chez '{entreprise}'. Voici l'offre :\n{description_offre}"

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

# Barre latérale (Sidebar) pour les paramètres
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Clé API OpenAI", type="password", help="Ta clé ne sera pas sauvegardée.")
    st.markdown("---")
    st.write("Cet outil génère des lettres sur-mesure et alimente automatiquement ton fichier Excel de suivi.")

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
            elif not entreprise or not poste or not description:
                st.warning("⚠️ Remplis au moins l'entreprise, le poste et la description.")
            else:
                with st.spinner("Rédaction en cours..."):
                    lettre = generer_lettre(api_key, entreprise, poste, description)
                    st.text_area("Lettre générée :", value=lettre, height=400)
                    
                    # Mise à jour de l'Excel en arrière-plan
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
