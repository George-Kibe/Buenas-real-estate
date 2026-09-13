import type { Metadata } from "next";

import ProfileView from "./ProfileView";

export const metadata: Metadata = { title: "My profile" };

export default function ProfilePage() {
  return <ProfileView />;
}
