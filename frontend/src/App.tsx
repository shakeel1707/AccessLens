import React from "react";
import { ScanForm } from "./components/ScanForm";
import { FindingsList } from "./components/FindingsList";
import { RepairReview } from "./components/RepairReview";
import { ReportDisplay } from "./components/ReportDisplay";
import { ProgressIndicator } from "./components/ProgressIndicator";
import "./App.css";

export const App: React.FC = () => {
  return (
    <div className="app">
      <header className="header">
        <h1>AccessLens</h1>
        <p>AI-powered website accessibility detection and repair</p>
      </header>

      <main className="main">
        <section className="section">
          <ProgressIndicator />
        </section>

        <section className="section">
          <ScanForm />
        </section>

        <section className="section">
          <FindingsList />
        </section>

        <section className="section">
          <RepairReview />
        </section>

        <section className="section">
          <ReportDisplay />
        </section>
      </main>

      <footer className="footer">
        <p>&copy; 2024 AccessLens. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default App;
