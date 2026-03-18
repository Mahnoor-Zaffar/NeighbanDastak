import { Navigate, createBrowserRouter } from "react-router-dom";

import { AuthGate } from "../components/AuthGate";
import { AppLayout } from "../components/AppLayout";
import { AppointmentCreatePage } from "../pages/AppointmentCreatePage";
import { AppointmentListPage } from "../pages/AppointmentListPage";
import { DemoAuthPage } from "../pages/DemoAuthPage";
import { PatientDetailPage } from "../pages/PatientDetailPage";
import { PatientFormPage } from "../pages/PatientFormPage";
import { PatientListPage } from "../pages/PatientListPage";
import { PrescriptionCreatePage } from "../pages/PrescriptionCreatePage";
import { PrescriptionDetailPage } from "../pages/PrescriptionDetailPage";
import { PrescriptionPrintPage } from "../pages/PrescriptionPrintPage";
import { QueuePage } from "../pages/QueuePage";
import { VisitCreatePage } from "../pages/VisitCreatePage";
import { VisitDetailPage } from "../pages/VisitDetailPage";

export const router = createBrowserRouter([
  {
    path: "/auth",
    element: <DemoAuthPage />,
  },
  {
    element: <AuthGate />,
    children: [
      {
        path: "/print/prescriptions/:prescriptionId",
        element: <PrescriptionPrintPage />,
      },
      {
        path: "/",
        element: <AppLayout />,
        children: [
          {
            index: true,
            element: <AppointmentListPage />,
          },
          {
            path: "appointments",
            element: <AppointmentListPage />,
          },
          {
            path: "appointments/new",
            element: <AppointmentCreatePage />,
          },
          {
            path: "queue",
            element: <QueuePage />,
          },
          {
            path: "visits/new",
            element: <VisitCreatePage />,
          },
          {
            path: "visits/:visitId",
            element: <VisitDetailPage />,
          },
          {
            path: "prescriptions/new",
            element: <PrescriptionCreatePage />,
          },
          {
            path: "prescriptions/:prescriptionId",
            element: <PrescriptionDetailPage />,
          },
          {
            path: "patients",
            element: <PatientListPage />,
          },
          {
            path: "patients/new",
            element: <PatientFormPage mode="create" />,
          },
          {
            path: "patients/:patientId",
            element: <PatientDetailPage />,
          },
          {
            path: "patients/:patientId/edit",
            element: <PatientFormPage mode="edit" />,
          },
          {
            path: "*",
            element: <Navigate replace to="/appointments" />,
          },
        ],
      },
    ],
  },
]);
