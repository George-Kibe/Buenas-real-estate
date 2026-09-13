"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import Spinner from "@/components/Spinner";
import { api, describeError } from "@/lib/api";
import { mediaUrl } from "@/lib/format";
import type { Profile, ProfileEnvelope } from "@/lib/types";
import { useAppSelector } from "@/store/hooks";

export default function ProfileView() {
  const router = useRouter();
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        // apps/profiles/renderers.py wraps the payload in a "Profile" key.
        const { data } = await api.get<ProfileEnvelope>("/profile/me/");
        if (!cancelled) setProfile(data.Profile);
      } catch (requestError) {
        if (!cancelled) setError(describeError(requestError, "Unable to load your profile"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    // loadUser() resolves before this renders, so an unset flag means signed out.
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, loading, router]);

  if (loading) return <Spinner label="Loading your profile" />;

  if (error || !profile) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <p className="surface-card rounded-xl p-8 text-center text-muted">
          {error ?? "Profile unavailable."}
        </p>
      </div>
    );
  }

  const roles = [
    profile.is_buyer && "Buyer",
    profile.is_seller && "Seller",
    profile.top_agent && "Top agent",
  ].filter(Boolean) as string[];

  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <div className="surface-card flex flex-col gap-6 rounded-xl p-6 sm:flex-row sm:items-center">
        <div className="relative size-24 shrink-0 overflow-hidden rounded-full bg-brand-50">
          <Image
            src={mediaUrl(profile.profile_photo)}
            alt=""
            fill
            sizes="96px"
            className="object-cover"
          />
        </div>
        <div>
          <h1 className="text-2xl font-bold">{profile.full_name.trim() || user?.username}</h1>
          <p className="text-muted">@{profile.username}</p>
          <p className="mt-1 text-sm text-muted">{profile.email}</p>
          {roles.length ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {roles.map((role) => (
                <span
                  key={role}
                  className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700"
                >
                  {role}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      <section className="surface-card mt-6 rounded-xl p-6">
        <h2 className="text-lg font-semibold">About</h2>
        <p className="mt-2 text-muted">{profile.about_me}</p>

        <dl className="mt-6 grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3">
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-muted">Phone</dt>
            <dd className="mt-0.5 font-medium">{profile.phone_number}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-muted">Location</dt>
            <dd className="mt-0.5 font-medium">
              {profile.city}, {profile.country}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-muted">Rating</dt>
            <dd className="mt-0.5 font-medium">
              {profile.rating ?? "—"} ({profile.num_reviews} review
              {profile.num_reviews === 1 ? "" : "s"})
            </dd>
          </div>
        </dl>
      </section>

      {profile.reviews.length ? (
        <section className="surface-card mt-6 rounded-xl p-6">
          <h2 className="text-lg font-semibold">Reviews</h2>
          <ul className="mt-4 space-y-4">
            {profile.reviews.map((review) => (
              <li key={review.id} className="border-t border-[var(--line)] pt-4 first:border-0 first:pt-0">
                <p className="font-medium">
                  {review.rater} · {review.rating}/5
                </p>
                <p className="mt-1 text-muted">{review.comment}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
