# Streamlit Layout Snippets (IMT 561)

These are short layout recipes you can adapt. They are intentionally minimal so you still have to connect them to your own dataframe and charts.

## Left panel layout (sidebar filters)
```python
st.sidebar.header("Filters")
# widgets go here
```

## Right panel layout (filters on the right)
```python
left, right = st.columns([3, 1])
with right:
    st.subheader("Filters")
    # widgets go here
with left:
    st.subheader("Main content")
    # charts/tables go here
```

## Top panel layout (filters on top)
```python
st.subheader("Filters")
c1, c2, c3 = st.columns(3)
with c1:
    borough = st.selectbox("Borough", options)
with c2:
    channel = st.selectbox("Channel", options)
with c3:
    rt = st.slider("Response time", 0.0, 30.0, (0.0, 10.0))
st.divider()
```

## Body with Header + 1 column
```python
st.title("Dashboard Title")
st.caption("1–2 sentence purpose statement.")
st.divider()
st.subheader("Main view")
```

## Body with Header + 2 columns
```python
st.title("Dashboard Title")
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.subheader("Chart A")
with col2:
    st.subheader("Chart B / Table")
```

## Body with Header + Tabs (3 tabs)
```python
st.title("Dashboard Title")
t1, t2, t3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])
with t1:
    st.subheader("View 1")
with t2:
    st.subheader("View 2")
with t3:
    st.subheader("View 3")
```
