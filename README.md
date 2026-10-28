Practical 5 — Simple Banking Application
I'll walk you through the complete process in VS Code on Windows, from creating the Python application to running both GitHub pushes and verifying the Kubernetes deployment.

Your practical requirements are:
- Push 1: Check balance and deposit money.
- Push 2: Add withdrawal functionality with balance validation.
- GitHub Actions must run tests, build a Docker image, push it to Docker Hub, and deploy the matching image to Kubernetes.
- Make exactly two source-code pushes to GitHub.
Step 1: Check your tools
Open VS Code, then open Terminal → New Terminal. Run these commands one at a time:
python --version
git --version
docker --version
kubectl get nodes


You should see version information for Python, Git, and Docker, and at least one Kubernetes node in the Ready state.

If your Kubernetes cluster is already running and your previous pods are working, you can use that cluster. Remember, GitHub Actions must also be able to reach it for automatic deployment.
Step 2: Create the project folder
In the VS Code terminal:
mkdir practical-5-banking
cd practical-5-banking
code .


Create this folder structure using the VS Code Explorer:
practical-5-banking/
├── app.py
├── test_app.py
├── requirements.txt
├── Dockerfile
├── deployment.yaml
├── service.yaml
└── .github/
    └── workflows/
        └── cicd.yml


Create the .github folder, then its workflows subfolder.
Step 3: Create the Python application for Push 1
Open app.py and paste this code. It implements balance checking and deposits.
from flask import Flask, request    return balance@app.route("/")def home():    return """    <h1>Simple Banking Application</h1>    <p>Use the options below.</p>    <form action="/deposit" method="post">        <input name="amount" type="number"               min="0.01" step="any"               placeholder="Deposit amount" required>        <button type="submit">Deposit</button>    </form>    <p><a href="/balance">Check Balance</a></p>    """@app.route("/balance")def check_balance():    return f"<h2>Current Balance: ₹{balance:.2f}</h2>"@app.route("/deposit", methods=["POST"])def deposit_route():    try:        amount = float(request.form["amount"])        new_balance = deposit(amount)        return f"<h2>New Balance: ₹{new_balance:.2f}</h2>"    except (ValueError, KeyError) as error:        return str(error), 400if __name__ == "__main__":    app.run(host="0.0.0.0", port=5000)



Save the file using Ctrl + S.
Step 4: Create automated tests for Push 1
Open test_app.py and paste:
import pytestimport app as bankingdef setup_function():    banking.balance = 1000.0def test_deposit():    assert banking.deposit(200) == 1200.0def test_invalid_deposit():    with pytest.raises(ValueError):        banking.deposit(-10)def test_balance_page():    response = banking.app.test_client().get("/balance")    assert response.status_code == 200    assert "1000.00" in response.get_data(as_text=True)def test_home_page():    assert banking.app.test_client().get("/").status_code == 200



These tests check whether depositing money works, invalid deposits are rejected, and the application pages respond successfully.
Step 5: Create the dependency file
Open requirements.txt and paste:
Flask>=3.1,<4.0
pytest>=8.0,<10.0


Step 6: Run the application locally
In the VS Code terminal, run:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -v


Expected result: 4 tests pass.

Now start the application:
python app.py


Open these URLs in your browser:
- Home page: http://localhost:5000
- Balance page: http://localhost:5000/balance
You should see an opening balance of ₹1000.00. Try depositing ₹200; the balance should become ₹1200.00.

Stop the local server using Ctrl + C in the terminal before proceeding.

Step 7: Create the Dockerfile
Create a file named Dockerfile with no file extension.

Paste:
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

CMD ["python", "-u", "app.py"]


This tells Docker how to package the application and run it inside a container.
Step 8: Create the Kubernetes Deployment
Create deployment.yaml:
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-banking
spec:
  replicas: 2
  selector:
    matchLabels:
      app: python-banking
  template:
    metadata:
      labels:
        app: python-banking
    spec:
      containers:
        - name: banking-app
          image: YOUR_DOCKERHUB_USERNAME/python-banking:bootstrap
          ports:
            - containerPort: 5000
          imagePullPolicy: Always


Replace YOUR_DOCKERHUB_USERNAME with your actual Docker Hub username.

The bootstrap tag is a placeholder. The GitHub Actions workflow will change the running Deployment to the unique image built by each push.
Step 9: Create the Kubernetes Service
Create service.yaml:
apiVersion: v1
kind: Service
metadata:
  name: python-banking-service
spec:
  type: NodePort
  selector:
    app: python-banking
  ports:
    - port: 80
      targetPort: 5000
      nodePort: 30080


This exposes the application through a Kubernetes Service.
Step 10: Create the GitHub Actions workflow
Inside .github/workflows/, create cicd.yml.

This workflow automatically tests, builds, pushes, and deploys the application whenever you push to the main branch.
name: Banking App CI-CD

on:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  build-test-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run automated tests
        run: python -m pytest -v

      - name: Generate unique image tag
        run: echo "IMAGE_TAG=${GITHUB_SHA::12}" >> "$GITHUB_ENV"

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/python-banking:${{ env.IMAGE_TAG }}

      - name: Configure Kubernetes
        env:
          KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
        run: |
          mkdir -p "$HOME/.kube"
          echo "$KUBE_CONFIG" | base64 -d > "$HOME/.kube/config"
          chmod 600 "$HOME/.kube/config"
          kubectl cluster-info

      - name: Apply Kubernetes manifests
        run: |
          kubectl apply -f deployment.yaml
          kubectl apply -f service.yaml

      - name: Deploy the image from this push
        run: |
          kubectl set image deployment/python-banking \
            banking-app=${{ secrets.DOCKERHUB_USERNAME }}/python-banking:${{ env.IMAGE_TAG }}

          kubectl rollout status deployment/python-banking --timeout=180s


Important: Configure GitHub secrets
Before the workflow can run successfully, create a GitHub repository and configure these three repository secrets:
Secret	What to enter
DOCKERHUB_USERNAME	Your Docker Hub username
DOCKERHUB_TOKEN	Your Docker Hub access token
KUBE_CONFIG	Base64-encoded kubeconfig for a cluster reachable by the GitHub Actions runner

Go to your repository on GitHub:

Settings → Secrets and variables → Actions → New repository secret

Do not paste passwords or tokens into your source code.

Kubernetes connectivity warning: If your cluster is running only on your Windows computer, a GitHub-hosted runner normally cannot access it directly. You need a reachable cluster or a properly configured self-hosted runner. The kubeconfig secret alone does not establish network connectivity.

Step 11: Create your GitHub repository
1. Open GitHub.
2. Create a new repository named practical-5-banking.
3. Keep track of its repository URL.
4. In VS Code, ensure you are in the project folder.
5. Check that all files are saved.
Run these commands for Push 1 only:
git init
git branch -M main
git add .
git commit -m "Push 1: Balance checking and deposits"
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main


Replace YOUR_GITHUB_REPOSITORY_URL with the actual URL of your repository.

If you already initialized Git and configured the remote, don't repeat those setup commands.
What happens after Push 1?
GitHub Actions checks out your code and installs dependencies.

Automated tests verify balance checking and deposits.

Docker builds and pushes the image with the first commit's unique tag.

Kubernetes deploys the image produced by Push 1.


To view the workflow, open your GitHub repository and select the Actions tab. Wait for the run to finish before proceeding.
Step 12: Modify the application for Push 2
Now add withdrawal functionality while keeping the existing balance checking and deposit features.

Open app.py and add this function below deposit():
def withdraw(amount):    global balance    if amount <= 0:        raise ValueError("Withdrawal must be positive")    if amount > balance:        raise ValueError("Insufficient balance")    balance -= amount    return balance



Inside the HTML returned by home(), add this form before the closing triple quotes:
<form action="/withdraw" method="post">
    <input name="amount" type="number"
           min="0.01" step="any"
           placeholder="Withdrawal amount" required>
    <button type="submit">Withdraw</button>
</form>


Add this route above the if __name__ == "__main__": section:
@app.route("/withdraw", methods=["POST"])def withdraw_route():    try:        amount = float(request.form["amount"])        new_balance = withdraw(amount)        return f"<h2>Remaining Balance: ₹{new_balance:.2f}</h2>"    except (ValueError, KeyError) as error:        return str(error), 400



Save app.py.
Step 13: Add tests for Push 2
Open test_app.py and append:
def test_withdrawal():    assert banking.withdraw(300) == 700.0def test_insufficient_balance():    with pytest.raises(ValueError, match="Insufficient balance"):        banking.withdraw(2000)def test_zero_withdrawal():    with pytest.raises(ValueError, match="positive"):        banking.withdraw(0)



Run the tests:
python -m pytest -v


Expected result: 7 tests pass.

The tests check that:
- Deposits still work.
- Balance checking still works.
- Valid withdrawals work.
- Withdrawals exceeding the balance are rejected.
- Zero-value withdrawals are rejected.
Step 14: Make Push 2
Once all tests pass, run:
git add .
git commit -m "Push 2: Add withdrawal and balance validation"
git push origin main


This is your second and final source-code push.

GitHub Actions should run again automatically. The new commit receives a different image tag, and Kubernetes updates to that exact image.
Step 15: Verify the result
After the second workflow succeeds, run these commands in a terminal connected to your Kubernetes cluster:
kubectl get deployments
kubectl get pods
kubectl get services
kubectl rollout status deployment/python-banking


Check the exact image running in Kubernetes:
kubectl get deployment python-banking -o jsonpath="{.spec.template.spec.containers[0].image}"


The image tag should match the second successful GitHub Actions run.

To access the application locally, run:
kubectl port-forward service/python-banking-service 8080:80


Open http://localhost:8080 in your browser.

Try these operations:
Expected demonstration results
Initial balance₹1,000


Deposit ₹200₹1,200


Withdraw ₹300₹900


Attempt to withdraw ₹2,000
Rejected


The balance examples assume each transaction starts from the original ₹1,000 balance. The application stores balance in memory, so this is an educational demonstration, not a real banking system. Multiple Kubernetes replicas also have separate in-memory balances.
