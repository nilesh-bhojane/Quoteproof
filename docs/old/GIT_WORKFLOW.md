# Git workflow for three contributors

## One-time setup by integrator
```bash
git init
git add .
git commit -m "chore: scaffold QuoteProof monorepo"
git branch -M main
git checkout -b dev
# Create the GitHub repository, then connect it:
git remote add origin https://github.com/ORG/REPO.git
git push -u origin main
git push -u origin dev
```

## Each contributor
Clone the same repository once:
```bash
git clone https://github.com/ORG/REPO.git
cd REPO
git checkout dev
git pull origin dev
git checkout -b feat/your-feature
```
Work only in the assigned folders, then:
```bash
git add path/to/your/feature
git commit -m "feat: describe your feature"
git push -u origin feat/your-feature
```
Open a Pull Request from `feat/your-feature` into `dev`.

## Integrator merge sequence
1. Merge Contributor A's PR into `dev`; run tests.
2. Merge Contributor B's PR into `dev`; resolve conflicts and run tests.
3. Merge Contributor C's PR into `dev`; resolve conflicts and run tests.
4. Run the full end-to-end demo; fix issues on `dev`.
5. Open PR `dev` → `main` and merge when stable.

## Keep work equivalent
- Agree on each feature's acceptance criteria before coding.
- Require a working component, tests/manual test steps, and a short handoff note from each contributor.
- Use PRs instead of sending ZIPs or overwriting each other's folders.
- If `dev` changes while someone is working, update their branch:
```bash
git checkout feat/your-feature
git fetch origin
git merge origin/dev
```
Resolve conflicts carefully, test, then push again.

Replace `ORG/REPO` with the actual GitHub repository. Do not push secrets or real customer data.
