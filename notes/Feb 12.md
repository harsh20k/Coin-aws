[[README.md]]

Why React
Many screens and shared state (auth, wallets, transactions, budgets, goals, AI chat) — React’s components and state keep this manageable.
Reusable UI (transaction rows, category selectors, cards, chat) fits a component-based approach.
Centralized state (current wallet, period, conversation, forms) is simpler than manual DOM updates.
Good ecosystem (routing, HTTP, UI libs) and a clear deploy path (build → S3/CloudFront).
When HTML/JS is enough
Only one or two pages and little interactivity, and you want no build step.
Summary: For this scope, React will scale better; use plain HTML/JS only if you intentionally keep the app very small.

## Login Research

Here are solid places to look:

### Official AWS Cognito docs
- **User Pools overview:**  
  https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools.html  
- **Authentication (sign-in, tokens, flows):**  
  https://docs.aws.amazon.com/cognito/latest/developerguide/authentication.html  
- **Authentication flows (password, SRP, MFA, etc.):**  
  https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-authentication-flow.html  
- **Hosted UI / managed login:**  
  https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-userpools-server-contract-reference.html  

### React + Cognito (Amplify)
- **Add auth and enable sign-up/sign-in/sign-out:**  
  https://docs.amplify.aws/gen1/react/build-a-backend/auth/enable-sign-up  
- **Set up Amplify Auth:**  
  https://docs.amplify.aws/gen1/react/build-a-backend/auth/set-up-auth  
- **Authenticator (prebuilt UI) config:**  
  https://ui.docs.amplify.aws/react/connected-components/authenticator/configuration  
- **Prescriptive guide (React + Cognito + Amplify UI):**  
  https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/authenticate-react-app-users-cognito-amplify-ui.html  

### Summary
- **Concepts and backend:** Cognito Developer Guide (first four links) — user pools, sign-up, login, session/tokens, Hosted UI.  
- **React app with sign-up, login, and session:** Amplify Auth docs + “Authenticate existing React application users” guide; use the **Authenticator** component for the fastest path to sign-up, sign-in, sign-out, and session handling.