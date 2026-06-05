import React from "react";
import Layout from "../components/layout/Layout";

const DashboardPage = () => {
  const cards = [
    {
      title: "Programs",
      value: 18,
    },
    {
      title: "Courses",
      value: 246,
    },
    {
      title: "SAR Reports",
      value: 32,
    },
    {
      title: "Readiness",
      value: "84%",
    },
  ];

  return (
    <Layout>
      <h1 className="text-3xl font-bold mb-8">
        Dashboard
      </h1>

      <div className="grid md:grid-cols-4 gap-6">
        {cards.map((card) => (
          <div
            key={card.title}
            className="bg-slate-900 p-6 rounded-xl border border-slate-800"
          >
            <p className="text-slate-400">
              {card.title}
            </p>

            <h2 className="text-4xl font-bold mt-3">
              {card.value}
            </h2>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-6 mt-8">
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
          <h2 className="font-semibold mb-4">
            Accreditation Progress
          </h2>

          <div className="w-full bg-slate-800 h-4 rounded-full">
            <div className="w-[84%] h-4 rounded-full bg-green-500" />
          </div>
        </div>

        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
          <h2 className="font-semibold mb-4">
            Recent Activity
          </h2>

          <ul className="space-y-3 text-slate-300">
            <li>CO-PO Mapping Updated</li>
            <li>SAR Generated</li>
            <li>Analytics Report Exported</li>
          </ul>
        </div>
      </div>
    </Layout>
  );
};

export default DashboardPage;
