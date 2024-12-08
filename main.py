import streamlit as st
import lanchain_helpr as lh

st.title("Geronimo-Test")

name = st.text_input("What is your name?")
company = st.text_input("What is your company name?")
country = st.text_input("What is your Country?")
position = st.selectbox(
    "What is your Job Role?",
    [
        "Developer/Engineer",
        "IT Execurtive",
        "C-Level",
        "Solution or System Architect",
        "Student",
        "Other",
    ],
)
interest = st.selectbox(
    "What is your Job Role?",
    [
        "API Management",
        "Integration",
        "Identity & Access Management",
        "Internal Developer Platform - Choreo",
        "Career Opportunities",
        "Other",
    ],
)
submit = st.button("Submit")

if submit:
    if name and company and position:
        st.write(f"Fetching data for {name} from {company} as a {position}")
        response = lh.generate_data(name, company, position,country)

        if response:
            
            #add person summary
            st.subheader("**Professional Summary:**")
            st.write(response.get("professional_summary", "No summary available"))
            
            #add social media links
            st.subheader("**Social Media Links:**")
            social_media_links = response.get("social_media_links", "")

            if social_media_links:
                # #uncomment this and delete bellow code to see the link
                st.write(social_media_links)

                # this code is user to show social media links using markdown
                links = social_media_links.split("\n")
                # for link in links:

                #     if link.strip():

                #         platform, url = (
                #             link.split(":", 1) if ":" in link else (None, None)
                #         )
                #         if platform and url:
                #             st.markdown(f"- [{platform.strip()}]({url.strip()})")
            else:
                st.write("No social media links found.")
                
            
             #add company summary
            st.subheader("**Company Details:**")
            st.write(f"**{company}**")
            st.write(response.get("company_summary", "No summary available"))

            st.subheader("**Additional Insights:**")
            st.write(
                response.get("additional_insights", "No additional insights available.")
            )

        else:
            st.write("Failed to generate data. Please try again.")
    else:
        st.write("Please fill in the required fields before submitting.")
