from google import genai
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="AI Systematic Review Screener", page_icon="📚", layout="wide"
)

st.title("📚 Systematic Review Title & Abstract Screener")
st.markdown(
    "Upload your search results CSV, define your criteria, and let AI screen your papers."
)

# Sidebar for configuration and API key
with st.sidebar:
  st.header("1. Configuration")
  api_key = st.text_input(
      "Enter Google Gemini API Key",
      type="password",
      help="Get a free key from Google AI Studio",
  )

  st.markdown("---")
  st.markdown(
      "### Need a Free API Key?\nGo to [Google AI Studio](https://aistudio.google.com/) to generate one for free."
  )

# Main container
col1, col2 = st.columns(2)

with col1:
  st.subheader("2. Define Eligibility Criteria")
  inclusion_criteria = st.text_area(
      "Inclusion Criteria",
      placeholder="e.g., Must be an RCT focusing on adults...",
      height=150,
  )

with col2:
  st.subheader("")
  exclusion_criteria = st.text_area(
      "Exclusion Criteria",
      placeholder="e.g., Animal studies, conference abstracts...",
      height=150,
  )

st.markdown("---")
st.subheader("3. Upload Dataset")
uploaded_file = st.file_uploader(
    "Upload your CSV search results file", type=["csv"]
)

if uploaded_file is not None:
  df = pd.read_csv(uploaded_file)
  st.success(
      f"File uploaded successfully! Total rows found: {len(df):,}"
  )

  st.write("Preview of your data:")
  st.dataframe(df.head(3))

  # Column mapping
  st.subheader("4. Map CSV Columns")
  columns = list(df.columns)
  c1, c2 = st.columns(2)
  with c1:
    title_col = st.selectbox(
        "Select Title Column",
        columns,
        index=columns.index("Title") if "Title" in columns else 0,
    )
  with c2:
    abstract_col = st.selectbox(
        "Select Abstract Column",
        columns,
        index=columns.index("Abstract") if "Abstract" in columns else 0,
    )

  # Run screening button
  if st.button("🚀 Run AI Screening", type="primary"):
    if not api_key:
      st.error("Please enter your Gemini API key in the sidebar first.")
    elif not inclusion_criteria:
      st.error("Please specify your inclusion criteria.")
    else:
      client = genai.Client(api_key=api_key)

      results_decision = []
      results_reason = []

      progress_bar = st.progress(0)
      status_text = st.empty()

      total_rows = len(df)

      for index, row in df.iterrows():
        status_text.text(
            f"Screening paper {index + 1} of {total_rows}..."
        )
        progress_bar.progress((index + 1) / total_rows)

        title = str(row.get(title_col, ""))
        abstract = str(row.get(abstract_col, ""))

        prompt = f"""
                You are an expert systematic reviewer. Screen the following paper based on the criteria provided.

                INCLUSION CRITERIA:
                {inclusion_criteria}

                EXCLUSION CRITERIA:
                {exclusion_criteria}

                PAPER TO SCREEN:
                Title: {title}
                Abstract: {abstract}

                Task: Decide whether to 'Include', 'Exclude', or mark as 'Unclear'.
                Format your exact answer as follows:
                Decision: [Include / Exclude / Unclear]
                Reason: [One brief sentence explaining why]
                """

        try:
          response = client.models.generate_content(
              model="gemini-2.5-flash", contents=prompt
          )
          text_resp = response.text

          # Simple parsing
          if "Decision:" in text_resp:
            parts = text_resp.split("Reason:")
            dec = (
                parts[0]
                .replace("Decision:", "")
                .strip()
                .split("\n")[0]
                .strip()
            )
            reas = parts[1].strip() if len(parts) > 1 else "No reason given."
          else:
            dec = "Unclear"
            reas = text_resp

          results_decision.append(dec)
          results_reason.append(reas)

        except Exception as e:
          results_decision.append("Error")
          results_reason.append(str(e))

      df["Screening_Decision"] = results_decision
      df["Screening_Reason"] = results_reason

      status_text.text("Screening completed!")
      st.success("All papers have been successfully screened!")

      st.dataframe(df)

      # Download button for results
      csv_data = df.to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 Download Screened CSV Results",
          data=csv_data,
          file_name="systematic_review_screened.csv",
          mime="text/csv",
      )
