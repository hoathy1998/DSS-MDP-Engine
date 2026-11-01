"""Phase 6: Streamlit demo of the MDP recommender (cf. Fig. 6 of the paper).

Page 1 – Koffer case simulation
  - sample or enter hidden true values; show current state (done items, known attributes)
  - table of allowed actions with expected profit, highlight the recommended one
  - user may pick any allowed action (including deviating); recommender continues from new state
  - at the end: realised profit vs the decision tree on the same case
Page 2 – Toy example (Section 5.3) to explain value of information

Run: streamlit run app/streamlit_app.py
"""
