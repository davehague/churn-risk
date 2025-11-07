AI Churn Risk App
Problem & Solution Overview

Problem:
We currently have hundreds of support tickets come in per week with general questions, technical support issues, account and plan inquiries, etc.
We have not been able to effectively identify and escalate frustrated customers or those that are “silently struggling”, both of which pose a “churn risk”.
We also have little to no way to identify recurring problems and themes of these customers to help drive the initiatives to prevent them in the future.
The best way to identify these recurring problems/themes is typically in the qualitative feedback aka “listening to them” which is very difficult at scale.
The challenge at scale is theming and organizing semantic customer data into a usable format to help drive organizational initiatives. (AI is the ideal technology for this challenge)
Because we have not been able to solve this challenge customers find their problems go unsolved, unescalated and keep recurring and therefore eventually cancel their account.
Worse, additional customers face the same problems as it is too difficult for us to identify systemic issues within our current system.
As a CEO, Owner, Customer Success Lead, Product Lead or other management team member… it is not feasible to be in the support inbox reviewing your customers tickets to spot trends and analyze ways to improve their experience or our product
However this is critical to reducing churn and delivering more value to your customers.

Target Company:
SMB/MM SaaS software with recurring subscription model ($200k+ ARR)
500+ support tickets per month
100+ customers
10-30 employees

Target Persona:
CEO/Owner, Customer Success Lead, Product Lead or other management team member
Currently struggling with reducing churn and prioritizing the product roadmap between new features, improved/optimized experiences, and bug prevention initiatives.
Keen to reduce churn and gain insights on product development to help grow the business
Looking for any easy way to identify high impact initiatives that align with our customer’s real and current problems… that vary by week/month/quarter.
And a way to ensure we are closing the loop on these issues and implementing solutions.


The solution this persona is seeking to implement will…
Identify, escalate, & action frustrated customers
Identify, escalate & action “significant support” customers
Identify, escalate & action “silently struggling” customers
Identify, Organize, & Analyze the recurring themes of these churn risk customers




App Requirements
#1 Identify, Escalate, & Action “Frustrated” Customers
Note: This is phase 1 version of the app should deliver immediate value upon initial login/sync. With a well trained AI on “negative sentiment” for software companies, this should be a wow moment upon the initial import/sync.

“Frustrated” Customers
The AI should be able to effectively identify customers that express negative sentiment via semantic context in a support ticket email
These tickets should have a meta field called “sentiment” in which they are labeled (very negative, negative, neutral, positive, very positive)
Eventually reporting on sentiment trends both positive and negative will be nice
Tickets that are labeled with a negative or very negative sentiment should create a “Churn Risk” card that will populate in a dashboard to be managed along with an alert to the user
Churn Risks cards should have the following associated data
Card Owner (app user)
Card Status
Contact Name & Email
Company Name & MRR
Direct link to support ticket
Support ticket topic(s) [see requirement #3]
Churn Risk cards should be presented in a Kanban board that can support saved views
Default view is all tickets with New, Working, Waiting, Completed
Sorted in New column descending by create date
Churn Risk cards should have a comment timeline in which you can tag users to be notified of the comment.
#2 Identify, Escalate, & Action “Significant Support” Customers
Note: This is a “phase 2” requirement. However I believe it is worth noting for foundational data model and development purposes.

“Significant Support” Customers
The app should be able to identify customers and companies that are deemed as “significant support” through data points that are pulled from the ticketing system.
Pre-configured triggers are created and able to be customized to determine “significant support” customers. 
Trigger: Support ticket with 10 emails sent in last 5 days 
Trigger: Company with 3 support tickets in last 7 days 
Trigger: Company with 25 total emails in last 30 days 

#3 Identify, Escalate, & Action “Silently Struggling” Customers
Note: This is a “phase 3” requirement and adds the most complexity & friction in onboarding. There is likely some human onboarding required (at least initially), but a lot of value to be unlocked.

“Silently Struggling” Customers
The app should be able to identify customers and companies that are deemed as “silently struggling” through data points that are pulled from the ticketing system and CRM. 
Product actions are required to be integrated to a field in the CRM vs direct app integration
These trigger rules would map to custom fields in the CRM and allow you create and/or conditional statements to trigger/create churn risk cards.
Some example of custom triggers that could be created with some light mapping / onboarding (all pulled via Hubspot (CRM) custom fields)
Trigger: Company without login in last 8 days 
Trigger: Company with registration date older than 30 days and onboarding step 3 not completed
Trigger: Company with > $999/mo MRR with less than 50 orders in last 30 days
#4 Identify, Organize, & Analyze the recurring themes of churn risks
Note: This is part of the initial scope to be rolled out with “phase 1” data. This can be simple initially but has a lot of opportunity to be built upon to unlock the most value for the customer with deep integration and data refinement.

Ticket Topics
Upon creation of a support ticket in the ticketing system / CRM, an AI will do two things:
Evaluate the ticket content to populate “sentiment”
Evaluate the ticket content to populate 1 or many “Ticket Topics”
During some phase of the initial onboarding of the app the most recent 200 tickets should be imported and analyzed to generate the groupings of ticket topics
The user will then analyze the roughly 6-12 different “ticket topics” and go through a process to merge, rename, and add new. 
While doing so they should be presented with a text box to add a prompt to why they merged, renamed, or added new topics that will train the AI
This is the secret sauce and one of the most difficult parts of the app to build, but adds the most value and stickiness.
Ideally the customer is periodically refining and training the AI to group tickets and topics better.
This can be done through manual addition, removal, or merging of topics on tickets while providing semantic feedback to why the action was taken…. on daily/weekly/monthly basis.
This could be done from both a dedicated UI and/or in a modal on another UI


Phase 1 Basic Reporting
In phase 1 you will only have “frustrated customer” churn risk cards and ideally accurate ticket topics
There are a few basic “views” I think that would be ideal to start.
Churn Risk View (default 30 days, but can be adjusted)
Number of churn risks by day for last 30 days in a bar chart segmented by ticket topic
Pie chart of ticket topics past 30 days
Line chart of ticket topics to see trends
Company View
A “leaderboard” type view of companies with the most churn alerts in the past 30 days. Ability to click/expand to get an idea of churn tickets associated.
Some kind of trend line graph to determine if a customer has an increase in churn tickets over a time period weighed again
Ticket Topic View
A word cloud type look to see the top and trending topics that are driving churn risk cards
Ideally a way to visualize and trend or anomalies over time periods


