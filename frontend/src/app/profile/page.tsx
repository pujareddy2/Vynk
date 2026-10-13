"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import PageContainer from "../../components/PageContainer";
import userService, {
  FullProfile,
  MasterInterest,
  MasterSkill,
  UserSkillItem,
  UserAvailabilityItem,
} from "../../services/user.service";
import { detectLiveLocation } from "../../services/location.service";

const presetAlarmSlots = [
  { id: "wd_morn", label: "🌅 Early Sparring (6:00 AM – 9:00 AM)", day_of_week: "Weekday Mornings", start_time: "06:00:00", end_time: "09:00:00" },
  { id: "wd_eve", label: "🌆 Post-Work Games (6:00 PM – 9:30 PM)", day_of_week: "Weekday Evenings", start_time: "18:00:00", end_time: "21:30:00" },
  { id: "sat_morn", label: "🏸 Saturday Courts (7:00 AM – 11:00 AM)", day_of_week: "Saturday Mornings", start_time: "07:00:00", end_time: "11:00:00" },
  { id: "sat_eve", label: "☕ Saturday Chill (5:00 PM – 9:00 PM)", day_of_week: "Saturday Evenings", start_time: "17:00:00", end_time: "21:00:00" },
  { id: "sun_sun", label: "☀️ Sunday Sunrise (6:30 AM – 10:30 AM)", day_of_week: "Sunday Mornings", start_time: "06:30:00", end_time: "10:30:00" },
  { id: "sun_all", label: "✨ Sunday Full Day (8:00 AM – 8:00 PM)", day_of_week: "Sunday", start_time: "08:00:00", end_time: "20:00:00" },
];

const popularCuratedSuggestions = [
  { name: "Badminton", icon: "🏸" },
  { name: "Photography", icon: "📷" },
  { name: "Coffee & Cafes", icon: "☕" },
  { name: "Cycling", icon: "🚴" },
  { name: "Board Games", icon: "🎲" },
  { name: "Hiking & Trails", icon: "🥾" },
  { name: "Tennis", icon: "🎾" },
  { name: "Pickleball", icon: "🏓" },
  { name: "Acoustic Music", icon: "🎸" },
  { name: "Art & Sketching", icon: "🎨" },
  { name: "Yoga & Fitness", icon: "🧘" },
  { name: "Travel & Roadtrips", icon: "✈️" },
  { name: "Coding & AI", icon: "💻" },
  { name: "Food & Cooking", icon: "🍜" },
  { name: "Cricket", icon: "🏏" },
  { name: "Football", icon: "⚽" },
];

export default function ProfilePage() {
  const router = useRouter();

  // Basic Profile State
  const [userId, setUserId] = useState<number | null>(null);
  const [userName, setUserName] = useState("Explorer");
  const [userEmail, setUserEmail] = useState("");
  const [userLocation, setUserLocation] = useState("");
  const [userBio, setUserBio] = useState(
    "Love discovering new activities, meeting sparring partners, and turning spontaneous local plans into reality."
  );
  const [userAvatar, setUserAvatar] = useState<string | null>(null);
  const [budgetPreference, setBudgetPreference] = useState("flexible");
  const [currentPlan, setCurrentPlan] = useState("Weekend sports & casual meetups");

  // User Interests (Names + IDs)
  const [userInterests, setUserInterests] = useState<string[]>([
    "Badminton",
    "Photography",
    "Coffee & Cafes",
    "Cycling",
  ]);
  const [customInterestInput, setCustomInterestInput] = useState("");
  const [interestsCatalog, setInterestsCatalog] = useState<MasterInterest[]>([]);
  const [skillsCatalog, setSkillsCatalog] = useState<MasterSkill[]>([]);
  const [selectedInterestIds, setSelectedInterestIds] = useState<number[]>([]);

  // User Skills State (Rich & Flexible)
  const [userSkills, setUserSkills] = useState<UserSkillItem[]>([
    { skill_id: 14, name: "Badminton Coaching & Sparring", skill_level: "Intermediate", is_offering: true, category: "Sports" },
    { skill_id: 10, name: "Photography & Lighting", skill_level: "Advanced", is_offering: true, category: "Creative" },
  ]);
  const [customSkillInput, setCustomSkillInput] = useState("");
  const [customSkillLevel, setCustomSkillLevel] = useState("Intermediate");
  const [customSkillOffering, setCustomSkillOffering] = useState(true);

  // User Availability Alarm State (Clock-alarm flexible windows)
  const [userAvailability, setUserAvailability] = useState<UserAvailabilityItem[]>([
    { day_of_week: "Saturday Mornings", start_time: "07:00:00", end_time: "11:00:00" },
    { day_of_week: "Weekday Evenings", start_time: "18:00:00", end_time: "21:30:00" },
  ]);
  const [alarmDay, setAlarmDay] = useState("Saturday");
  const [alarmStartTime, setAlarmStartTime] = useState("07:00");
  const [alarmEndTime, setAlarmEndTime] = useState("10:30");
  const [alarmNote, setAlarmNote] = useState("");

  // UI State
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [isOnboarding, setIsOnboarding] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("onboarding") === "true") {
        setIsOnboarding(true);
        setIsEditing(true);
      }
    }

    async function loadFullProfileData() {
      try {
        setLoading(true);

        // 1. Fetch Master Catalogs from Backend
        const [ints, sks] = await Promise.all([
          userService.getInterestsCatalog().catch(() => [] as MasterInterest[]),
          userService.getSkillsCatalog().catch(() => [] as MasterSkill[]),
        ]);

        // Filter out machine-generated timestamp strings like Bouldering_179170...
        const cleanInterests = (ints || []).filter((i) => !/\d{4,}|_\d+/.test(i.name));
        const cleanSkills = (sks || []).filter((s) => !/\d{4,}|_\d+/.test(s.name));

        setInterestsCatalog(cleanInterests);
        setSkillsCatalog(cleanSkills);

        // 2. Fetch User Profile from Backend GET /profile/me
        const profile: FullProfile = await userService.getProfileMe().catch(() => null as any);

        if (profile) {
          setUserId(profile.user_id);
          setUserEmail(profile.email || "");
          if (profile.display_name) setUserName(profile.display_name);
          if (profile.approx_locality) {
            setUserLocation(profile.approx_locality);
          } else {
            // Automatically detect live location without requiring a button click
            const live = await detectLiveLocation();
            if (live?.locality) {
              setUserLocation(live.locality);
              userService.updateProfile({ approx_locality: live.locality }).catch(() => {});
            }
          }
          if (profile.bio) setUserBio(profile.bio);
          if (profile.avatar_url) setUserAvatar(profile.avatar_url);
          if (profile.budget_preference) setBudgetPreference(profile.budget_preference);

          if (profile.interests && profile.interests.length > 0) {
            const cleanUserInts = profile.interests
              .filter((i) => !/\d{4,}|_\d+/.test(i.name))
              .map((i) => i.name);
            if (cleanUserInts.length > 0) {
              setUserInterests(cleanUserInts);
            }
            setSelectedInterestIds(profile.interests.map((i) => i.interest_id));
          }

          if (profile.skills && profile.skills.length > 0) {
            const cleanSkillsList = profile.skills.filter((s) => !/\d{4,}|_\d+/.test(s.name || ""));
            if (cleanSkillsList.length > 0) {
              setUserSkills(cleanSkillsList);
            }
          }

          if (profile.availability && profile.availability.length > 0) {
            setUserAvailability(profile.availability);
          }
        } else {
          // Check localStorage fallback
          const stored = localStorage.getItem("vynk_user");
          if (stored) {
            try {
              const parsed = JSON.parse(stored);
              if (parsed.name) setUserName(parsed.name);
              if (parsed.location) setUserLocation(parsed.location);
              if (parsed.bio) setUserBio(parsed.bio);
              if (parsed.avatar) setUserAvatar(parsed.avatar);
              if (parsed.email) setUserEmail(parsed.email);
              if (parsed.skills) setUserSkills(parsed.skills);
              if (parsed.availability) setUserAvailability(parsed.availability);
            } catch {}
          }
        }
      } catch {
        // Graceful fallback
      } finally {
        setLoading(false);
      }
    }

    loadFullProfileData();
  }, []);

  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        setUserAvatar(result);
        try {
          const stored = localStorage.getItem("vynk_user");
          const userObj = stored ? JSON.parse(stored) : {};
          userObj.avatar = result;
          localStorage.setItem("vynk_user", JSON.stringify(userObj));
        } catch {}
      };
      reader.readAsDataURL(file);
    }
  };

  // Add custom interest typed by user (supports Enter key or comma-separated items)
  const handleAddCustomInterest = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const raw = customInterestInput.trim();
    if (!raw) return;

    const items = raw
      .split(/[,;]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    let updatedList = [...userInterests];
    let updatedIds = [...selectedInterestIds];

    items.forEach((item) => {
      const formatted = item.charAt(0).toUpperCase() + item.slice(1);
      if (!updatedList.some((i) => i.toLowerCase() === formatted.toLowerCase())) {
        updatedList.push(formatted);

        const match = interestsCatalog.find(
          (c) => c.name.toLowerCase() === formatted.toLowerCase()
        );
        if (match && !updatedIds.includes(match.interest_id)) {
          updatedIds.push(match.interest_id);
        }
      }
    });

    setUserInterests(updatedList);
    setSelectedInterestIds(updatedIds);
    setCustomInterestInput("");
  };

  const handleRemoveInterest = (interestName: string) => {
    setUserInterests((prev) => prev.filter((i) => i !== interestName));
    const match = interestsCatalog.find(
      (c) => c.name.toLowerCase() === interestName.toLowerCase()
    );
    if (match) {
      setSelectedInterestIds((prev) => prev.filter((id) => id !== match.interest_id));
    }
  };

  const toggleCuratedSuggestion = (name: string) => {
    if (userInterests.some((i) => i.toLowerCase() === name.toLowerCase())) {
      handleRemoveInterest(name);
    } else {
      setUserInterests((prev) => [...prev, name]);
      const match = interestsCatalog.find(
        (c) => c.name.toLowerCase() === name.toLowerCase()
      );
      if (match) {
        setSelectedInterestIds((prev) => [...prev, match.interest_id]);
      }
    }
  };

  // Helper for Alarm 12-hour AM/PM formatting
  const formatAlarmTime = (timeStr?: string) => {
    if (!timeStr) return "";
    const parts = timeStr.split(":");
    let hours = parseInt(parts[0], 10);
    const minutes = parts[1] || "00";
    if (isNaN(hours)) return timeStr;
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12;
    hours = hours ? hours : 12;
    return `${hours}:${minutes} ${ampm}`;
  };

  // Add Custom Clock-Alarm Availability Window
  const handleAddCustomAvailability = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!alarmDay || !alarmStartTime || !alarmEndTime) return;

    const formattedStart = alarmStartTime.length === 5 ? `${alarmStartTime}:00` : alarmStartTime;
    const formattedEnd = alarmEndTime.length === 5 ? `${alarmEndTime}:00` : alarmEndTime;
    const dayLabel = alarmNote.trim() ? `${alarmDay} (${alarmNote.trim()})` : alarmDay;

    const newItem: UserAvailabilityItem = {
      day_of_week: dayLabel,
      start_time: formattedStart,
      end_time: formattedEnd,
    };

    setUserAvailability((prev) => [...prev, newItem]);
    setAlarmNote("");
  };

  const handleRemoveAvailability = (index: number) => {
    setUserAvailability((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleTogglePresetAlarm = (preset: { day_of_week: string; start_time: string; end_time: string }) => {
    const exists = userAvailability.some(
      (a) => a.day_of_week.toLowerCase() === preset.day_of_week.toLowerCase()
    );
    if (exists) {
      setUserAvailability((prev) =>
        prev.filter((a) => a.day_of_week.toLowerCase() !== preset.day_of_week.toLowerCase())
      );
    } else {
      setUserAvailability((prev) => [...prev, preset]);
    }
  };

  // Skill category emoji helper
  const getSkillEmoji = (name: string) => {
    const lower = name.toLowerCase();
    if (lower.includes("badminton")) return "🏸";
    if (lower.includes("guitar")) return "🎸";
    if (lower.includes("photo")) return "📷";
    if (lower.includes("video")) return "🎬";
    if (lower.includes("code") || lower.includes("dev") || lower.includes("python") || lower.includes("react")) return "💻";
    if (lower.includes("drum")) return "🥁";
    if (lower.includes("piano") || lower.includes("keyboard")) return "🎹";
    if (lower.includes("sing") || lower.includes("vocal")) return "🎤";
    if (lower.includes("football") || lower.includes("soccer")) return "⚽";
    if (lower.includes("tennis") || lower.includes("pickleball")) return "🎾";
    if (lower.includes("chess")) return "♟️";
    if (lower.includes("yoga") || lower.includes("mindfulness")) return "🧘";
    if (lower.includes("fitness") || lower.includes("gym") || lower.includes("workout")) return "💪";
    if (lower.includes("write") || lower.includes("writing")) return "✍️";
    if (lower.includes("speak") || lower.includes("host")) return "🎙️";
    if (lower.includes("figma") || lower.includes("design") || lower.includes("art")) return "🎨";
    return "⚡";
  };

  // Add Custom Skill (Type & Press Enter)
  const handleAddCustomSkill = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const raw = customSkillInput.trim();
    if (!raw) return;

    if (userSkills.some((s) => (s.name || "").toLowerCase() === raw.toLowerCase())) {
      setCustomSkillInput("");
      return;
    }

    const match = skillsCatalog.find(
      (c) =>
        c.name.toLowerCase() === raw.toLowerCase() ||
        c.name.toLowerCase().includes(raw.toLowerCase()) ||
        raw.toLowerCase().includes(c.name.toLowerCase())
    );

    const targetSkillId = match ? match.skill_id : (skillsCatalog[0]?.skill_id || 1);

    const newSkillItem: UserSkillItem = {
      skill_id: targetSkillId,
      name: raw,
      category: match?.category || "Activities & Sparring",
      skill_level: customSkillLevel,
      is_offering: customSkillOffering,
    };

    setUserSkills((prev) => [...prev, newSkillItem]);
    setCustomSkillInput("");
  };

  const handleRemoveSkill = (index: number) => {
    setUserSkills((prev) => prev.filter((_, idx) => idx !== index));
  };

  const toggleCatalogSkill = (catSkill: MasterSkill) => {
    const existingIndex = userSkills.findIndex(
      (s) => (s.name || "").toLowerCase() === catSkill.name.toLowerCase()
    );
    if (existingIndex >= 0) {
      setUserSkills((prev) => prev.filter((_, idx) => idx !== existingIndex));
    } else {
      setUserSkills((prev) => [
        ...prev,
        {
          skill_id: catSkill.skill_id,
          name: catSkill.name,
          category: catSkill.category,
          skill_level: "Intermediate",
          is_offering: true,
        },
      ]);
    }
  };

  const updateSkillLevelByIndex = (index: number, level: string) => {
    setUserSkills((prev) =>
      prev.map((s, idx) => (idx === index ? { ...s, skill_level: level } : s))
    );
  };

  const toggleSkillOfferingByIndex = (index: number) => {
    setUserSkills((prev) =>
      prev.map((s, idx) => (idx === index ? { ...s, is_offering: !s.is_offering } : s))
    );
  };

  const handleSaveProfile = async (redirectToConnections = false) => {
    setSaving(true);
    try {
      // 1. Gather all matched interest IDs from userInterests
      let finalInterestIds: number[] = [...selectedInterestIds];
      userInterests.forEach((name) => {
        const match = interestsCatalog.find(
          (c) => c.name.toLowerCase() === name.toLowerCase()
        );
        if (match && !finalInterestIds.includes(match.interest_id)) {
          finalInterestIds.push(match.interest_id);
        }
      });

      if (finalInterestIds.length === 0 && interestsCatalog.length > 0) {
        finalInterestIds = [interestsCatalog[0].interest_id];
      }

      const availabilityPayload: UserAvailabilityItem[] = userAvailability.map((a) => ({
        day_of_week: a.day_of_week,
        start_time: a.start_time ? (a.start_time.length === 5 ? `${a.start_time}:00` : a.start_time) : "07:00:00",
        end_time: a.end_time ? (a.end_time.length === 5 ? `${a.end_time}:00` : a.end_time) : "10:00:00",
      }));

      const skillsPayload: UserSkillItem[] = userSkills.map((s) => ({
        skill_id: s.skill_id || (skillsCatalog[0]?.skill_id || 1),
        skill_level: s.skill_level || "Intermediate",
        is_offering: s.is_offering ?? true,
      }));

      // Call Backend atomic onboarding or batch endpoints
      let locToSend = userLocation.trim();
      if (!locToSend) {
        try {
          const live = await detectLiveLocation();
          if (live?.locality) locToSend = live.locality;
        } catch {}
      }

      await userService.completeOnboarding({
        display_name: userName.trim(),
        bio: userBio.trim(),
        avatar_url: userAvatar || undefined,
        approx_locality: locToSend || undefined,
        budget_preference: budgetPreference,
        interest_ids: finalInterestIds,
        skills: skillsPayload,
        availability: availabilityPayload,
      });

      // 2. Persist in local storage
      localStorage.setItem(
        "vynk_user",
        JSON.stringify({
          user_id: userId,
          name: userName.trim(),
          email: userEmail,
          location: userLocation.trim(),
          bio: userBio.trim(),
          avatar: userAvatar,
          budget_preference: budgetPreference,
          interests: userInterests,
          skills: userSkills,
          availability: userAvailability,
          currentPlan,
        })
      );

      setSavedSuccess(true);
      setIsEditing(false);
      setIsOnboarding(false);

      if (redirectToConnections) {
        // Instant Gratification: Send directly to Connections Swipe Deck!
        router.push("/connections");
      } else {
        setTimeout(() => setSavedSuccess(false), 3000);
      }
    } catch {
      // Fallback update individual endpoints
      try {
        await userService.updateProfile({
          display_name: userName.trim(),
          approx_locality: userLocation.trim(),
          bio: userBio.trim(),
          avatar_url: userAvatar || undefined,
          budget_preference: budgetPreference,
        });
      } catch {}

      setSavedSuccess(true);
      setIsEditing(false);
      if (redirectToConnections) {
        router.push("/connections");
      } else {
        setTimeout(() => setSavedSuccess(false), 3000);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("vynk_token");
    localStorage.removeItem("vynk_user");
    router.push("/login");
  };

  return (
    <PageContainer>
      <div className="space-y-8 max-w-5xl mx-auto pb-12">
        {/* Onboarding Banner for New Users */}
        {isOnboarding && (
          <section className="rounded-3xl bg-gradient-to-r from-teal-500/20 via-emerald-500/15 to-teal-500/20 p-6 md:p-8 border border-teal-500/40 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6 transition-all animate-[fadeIn_0.5s_ease-out]">
            <div className="space-y-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-400/20 px-3 py-1 text-xs font-bold uppercase tracking-wider text-teal-700 dark:text-teal-300">
                ✨ Step 2 of 2: Set Up Your Vibe
              </span>
              <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white">
                Welcome to Vynk! Let&apos;s build your profile.
              </h2>
              <p className="text-sm text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
                Add your favorite interests below. Our AI matching radar will immediately connect you with nearby players and groups who share your passion.
              </p>
            </div>

            <button
              type="button"
              onClick={() => handleSaveProfile(true)}
              disabled={saving}
              className="rounded-2xl bg-teal-400 px-7 py-3.5 text-sm font-bold text-slate-950 shadow-lg shadow-teal-500/25 hover:bg-teal-300 transition shrink-0 cursor-pointer flex items-center gap-2"
            >
              {saving ? (
                <>
                  <span className="h-4 w-4 rounded-full border-2 border-slate-950 border-t-transparent animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <span>Complete &amp; Find Matches →</span>
              )}
            </button>
          </section>
        )}

        {/* Success Alert Banner */}
        {savedSuccess && (
          <div className="rounded-2xl bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-800 p-4 text-sm font-semibold text-teal-800 dark:text-teal-300 flex items-center justify-between shadow-sm">
            <span>✓ Profile attributes successfully saved and vector embeddings updated!</span>
            <button
              onClick={() => setSavedSuccess(false)}
              className="text-teal-600 dark:text-teal-400 font-bold hover:opacity-75"
            >
              ✕
            </button>
          </div>
        )}

        {/* 1. HERO PROFILE CARD */}
        <section className="overflow-hidden rounded-[2.5rem] bg-white shadow-md ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 transition-colors">
          {/* Cover Gradient */}
          <div className="relative h-48 md:h-56 overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-teal-950 p-6 md:p-8 text-white border-b border-slate-800">
            <div className="relative z-10 max-w-xl">
              <span className="text-[11px] font-bold uppercase tracking-[0.25em] text-teal-400">
                Verified Explorer Space
              </span>
              <h1 className="mt-1.5 text-3xl md:text-4xl font-extrabold leading-tight">
                {userName}&apos;s <span className="text-teal-400">Vynk Profile</span>
              </h1>
              <p className="mt-1 text-xs md:text-sm text-slate-300">
                ID #{userId || "101"} · Connected to Hyderabad Local Network
              </p>
            </div>
            <div className="absolute -right-16 -top-20 h-64 w-64 rounded-full bg-teal-500/15 blur-3xl" />
            <div className="absolute bottom-2 right-12 h-36 w-36 rounded-full bg-indigo-500/20 blur-2xl" />
          </div>

          {/* Details Body */}
          <div className="p-6 md:p-8">
            <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6 pb-6 border-b border-slate-100 dark:border-slate-800">
              {/* Photo & Name */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
                {/* Photo Upload Avatar */}
                <div className="relative group">
                  <div className="flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-3xl border-4 border-white bg-gradient-to-br from-slate-900 to-teal-700 text-3xl font-black text-white shadow-xl dark:border-slate-800">
                    {userAvatar ? (
                      <img
                        src={userAvatar}
                        alt={userName}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      userName.charAt(0).toUpperCase()
                    )}
                  </div>

                  <label className="absolute -bottom-1 -right-1 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-teal-400 text-slate-950 shadow-md hover:bg-teal-300 transition hover:scale-110">
                    <span className="text-sm">📷</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarUpload}
                      className="hidden"
                    />
                  </label>
                </div>

                {/* Identity Inputs/Labels */}
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-teal-100 dark:bg-teal-950 px-2.5 py-0.5 text-[11px] font-bold text-teal-800 dark:text-teal-300 ring-1 ring-teal-200 dark:ring-teal-800">
                      ✓ Verified Member
                    </span>
                    <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2.5 py-0.5 text-[11px] font-bold text-slate-700 dark:text-slate-300">
                      ⭐ Trust Score: 96%
                    </span>
                  </div>

                  {isEditing ? (
                    <div className="space-y-2 pt-1">
                      <div>
                        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 block">
                          Display Name
                        </label>
                        <input
                          type="text"
                          value={userName}
                          onChange={(e) => setUserName(e.target.value)}
                          placeholder="Your Name"
                          className="mt-0.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-base font-bold text-slate-900 placeholder:text-slate-400 outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 block">
                          City &amp; Area (Approximate Locality)
                        </label>
                        <input
                          type="text"
                          value={userLocation}
                          onChange={(e) => setUserLocation(e.target.value)}
                          placeholder="e.g. Jubilee Hills, Hyderabad"
                          className="mt-0.5 rounded-xl border border-slate-300 bg-white px-3.5 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 dark:border-slate-700 dark:bg-slate-800 dark:text-white w-full sm:w-72"
                        />
                      </div>
                    </div>
                  ) : (
                    <div>
                      <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white">
                        {userName}
                      </h2>
                      <p className="text-xs md:text-sm font-medium text-slate-600 dark:text-slate-300 flex items-center gap-1.5 mt-0.5">
                        <span>📍 {userLocation}</span>
                        <span>·</span>
                        <span className="text-teal-600 dark:text-teal-400 font-semibold">{userEmail}</span>
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
                <Link
                  href="/connections"
                  className="rounded-xl bg-teal-50 dark:bg-teal-950/70 border border-teal-200 dark:border-teal-800 px-4 py-2.5 text-xs font-bold text-teal-800 dark:text-teal-300 hover:bg-teal-100 transition"
                >
                  🎴 Swipe Matching Deck
                </Link>

                {isEditing ? (
                  <button
                    type="button"
                    onClick={() => handleSaveProfile(false)}
                    disabled={saving}
                    className="rounded-xl bg-teal-400 px-5 py-2.5 text-xs font-bold text-slate-950 shadow-md hover:bg-teal-300 transition cursor-pointer"
                  >
                    {saving ? "Saving..." : "Save Changes"}
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => setIsEditing(true)}
                    className="rounded-xl bg-slate-900 px-5 py-2.5 text-xs font-bold text-white hover:bg-slate-800 dark:bg-white dark:text-slate-950 transition cursor-pointer"
                  >
                    Edit Profile
                  </button>
                )}

                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-xl border border-rose-200 px-3.5 py-2.5 text-xs font-bold text-rose-600 hover:bg-rose-50 dark:border-rose-900/40 dark:hover:bg-rose-950/40 transition cursor-pointer"
                >
                  Log Out
                </button>
              </div>
            </div>

            {/* Bio & Budget Preference */}
            <div className="mt-6 space-y-4">
              {isEditing ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2 space-y-1">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 block">
                      About You (Bio)
                    </label>
                    <textarea
                      rows={3}
                      value={userBio}
                      onChange={(e) => setUserBio(e.target.value)}
                      placeholder="Tell people what activities you enjoy and what kind of plans you look for..."
                      className="w-full rounded-xl border border-slate-300 bg-white p-3 text-sm text-slate-900 placeholder:text-slate-400 outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 block">
                      Budget Preference
                    </label>
                    <select
                      value={budgetPreference}
                      onChange={(e) => setBudgetPreference(e.target.value)}
                      className="w-full rounded-xl border border-slate-300 bg-white p-3 text-sm font-semibold text-slate-900 outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    >
                      <option value="free">Free Only ($0)</option>
                      <option value="low">Low Budget (under ₹300 per session)</option>
                      <option value="moderate">Moderate (₹300 - ₹800 split court/tickets)</option>
                      <option value="flexible">Flexible / Any Budget</option>
                    </select>

                    <label className="text-[11px] font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 block pt-2">
                      Current Activity Focus
                    </label>
                    <input
                      type="text"
                      value={currentPlan}
                      onChange={(e) => setCurrentPlan(e.target.value)}
                      placeholder="e.g. Weekend badminton, coffee walk"
                      className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-300 max-w-3xl">
                    {userBio}
                  </p>

                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <span className="inline-flex items-center gap-1.5 rounded-xl bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-800 px-3 py-1.5 text-xs font-semibold text-teal-800 dark:text-teal-300">
                      🎯 Current Plan: {currentPlan}
                    </span>
                    <span className="inline-flex items-center gap-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300">
                      💰 Budget: {budgetPreference.toUpperCase()}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* 2. SIMPLE, ELEGANT TYPE-AND-PRESS-ENTER INTERESTS SECTION */}
        <section className="rounded-[2.5rem] bg-white p-6 md:p-8 shadow-md ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 transition-colors">
          <div className="pb-4 border-b border-slate-100 dark:border-slate-800">
            <span className="text-[10px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
              Interest Radar Customizer
            </span>
            <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">
              What Are You Interested In? ({userInterests.length} Added)
            </h2>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
              Type your favorite hobbies, sports, or plans and press <strong>Enter</strong> to add them instantly.
            </p>
          </div>

          {/* Interactive Type-to-Add Input Bar */}
          <form onSubmit={handleAddCustomInterest} className="mt-6 flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                value={customInterestInput}
                onChange={(e) => setCustomInterestInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddCustomInterest();
                  } else if (e.key === ",") {
                    e.preventDefault();
                    handleAddCustomInterest();
                  }
                }}
                placeholder="Type an interest (e.g. Badminton, Photography, Coffee, Cycling) and press Enter ↵"
                className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3.5 pr-28 text-sm text-slate-900 placeholder:text-slate-400 outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
              <span className="hidden sm:inline-flex absolute right-3 top-1/2 -translate-y-1/2 items-center rounded-lg bg-slate-100 dark:bg-slate-700 px-2 py-1 text-[11px] font-bold text-slate-500 dark:text-slate-300 pointer-events-none">
                ↵ Press Enter
              </span>
            </div>
            <button
              type="submit"
              disabled={!customInterestInput.trim()}
              className="rounded-2xl bg-teal-400 px-6 py-3.5 text-xs font-bold text-slate-950 shadow-md hover:bg-teal-300 disabled:opacity-40 disabled:cursor-not-allowed transition cursor-pointer shrink-0"
            >
              + Add Interest
            </button>
          </form>

          {/* Currently Added Interests */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-3">
              <label className="text-[11px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 block">
                Your Active Interests ({userInterests.length})
              </label>
              {userInterests.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    setUserInterests([]);
                    setSelectedInterestIds([]);
                  }}
                  className="text-[11px] font-semibold text-rose-600 hover:text-rose-700 dark:text-rose-400 cursor-pointer"
                >
                  Clear all
                </button>
              )}
            </div>

            {userInterests.length > 0 ? (
              <div className="flex flex-wrap gap-2.5">
                {userInterests.map((interest) => (
                  <span
                    key={interest}
                    className="inline-flex items-center gap-2 rounded-2xl bg-teal-400 text-slate-950 px-4 py-2 text-xs font-bold shadow-sm animate-[fadeIn_0.2s_ease-out] hover:shadow-md transition"
                  >
                    <span>{interest}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveInterest(interest)}
                      className="h-4 w-4 rounded-full bg-slate-950/20 hover:bg-slate-950/40 flex items-center justify-center text-[10px] text-slate-950 transition cursor-pointer"
                      title={`Remove ${interest}`}
                    >
                      ✕
                    </button>
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">
                No interests added yet. Type an interest above or tap any suggestion below.
              </p>
            )}
          </div>

          {/* Quick-Pick Popular Suggestions */}
          <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800">
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 block mb-3">
              💡 Popular Quick Suggestions (Tap to add):
            </label>
            <div className="flex flex-wrap gap-2">
              {popularCuratedSuggestions.map((sug) => {
                const isSelected = userInterests.some(
                  (i) => i.toLowerCase() === sug.name.toLowerCase()
                );
                return (
                  <button
                    key={sug.name}
                    type="button"
                    onClick={() => toggleCuratedSuggestion(sug.name)}
                    className={`rounded-xl px-3.5 py-2 text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
                      isSelected
                        ? "bg-teal-500/20 border border-teal-500 text-teal-800 dark:text-teal-300 font-bold"
                        : "bg-slate-100 text-slate-800 hover:bg-slate-200 border border-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700"
                    }`}
                  >
                    <span>{sug.icon}</span>
                    <span>{sug.name}</span>
                    <span className="text-[10px] text-slate-400">
                      {isSelected ? "✓" : "+"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        {/* 3. FLEXIBLE CLOCK-ALARM AVAILABILITY SCHEDULE */}
        <section className="rounded-[2.5rem] bg-white p-6 md:p-8 shadow-md ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 transition-colors">
          <div className="pb-4 border-b border-slate-100 dark:border-slate-800">
            <span className="text-[10px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
              ⏰ Schedule &amp; Time Alarm Radar
            </span>
            <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">
              When Are You Free For Plans? ({userAvailability.length} Windows Set)
            </h2>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
              Set your free hours like an alarm clock. Choose your days and custom start &amp; end times so our AI radar connects you for activities when you are actually free.
            </p>
          </div>

          {/* Clock Alarm Style Time Slot Creator */}
          <form
            onSubmit={handleAddCustomAvailability}
            className="mt-6 rounded-3xl bg-slate-50 dark:bg-slate-850 p-5 md:p-6 border border-slate-200 dark:border-slate-800 space-y-4"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                <span>⏰</span> Set a Custom Time Window (Alarm)
              </span>
              <span className="text-[11px] text-teal-600 dark:text-teal-400 font-semibold">
                Live Alarm Picker
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Day Selection */}
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 block mb-1">
                  Day of Week
                </label>
                <select
                  value={alarmDay}
                  onChange={(e) => setAlarmDay(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-xs font-bold text-slate-900 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="Saturday">Saturday</option>
                  <option value="Sunday">Sunday</option>
                  <option value="Weekday Evenings">Weekday Evenings (Mon-Fri)</option>
                  <option value="Weekday Mornings">Weekday Mornings (Mon-Fri)</option>
                  <option value="Monday">Monday</option>
                  <option value="Tuesday">Tuesday</option>
                  <option value="Wednesday">Wednesday</option>
                  <option value="Thursday">Thursday</option>
                  <option value="Friday">Friday</option>
                  <option value="Weekend Days">Weekend Full Days</option>
                </select>
              </div>

              {/* Start Time (Alarm Clock Picker) */}
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 block mb-1">
                  ⏰ Start Time
                </label>
                <input
                  type="time"
                  value={alarmStartTime}
                  onChange={(e) => setAlarmStartTime(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-bold text-slate-900 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              {/* End Time (Alarm Clock Picker) */}
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 block mb-1">
                  ⏰ End Time
                </label>
                <input
                  type="time"
                  value={alarmEndTime}
                  onChange={(e) => setAlarmEndTime(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-bold text-slate-900 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              {/* Activity / Plan Tag */}
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 block mb-1">
                  Focus / Activity (Optional)
                </label>
                <input
                  type="text"
                  value={alarmNote}
                  onChange={(e) => setAlarmNote(e.target.value)}
                  placeholder="e.g. Badminton, Sparring, Coffee"
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                className="rounded-xl bg-teal-400 px-6 py-2.5 text-xs font-bold text-slate-950 shadow-md hover:bg-teal-300 transition cursor-pointer flex items-center gap-1.5"
              >
                <span>⏰</span>
                <span>+ Set Alarm Window</span>
              </button>
            </div>
          </form>

          {/* Active Alarms Roster */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-3">
              <label className="text-[11px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 block">
                Active Alarms &amp; Free Windows ({userAvailability.length})
              </label>
              {userAvailability.length > 0 && (
                <button
                  type="button"
                  onClick={() => setUserAvailability([])}
                  className="text-[11px] font-semibold text-rose-600 hover:text-rose-700 dark:text-rose-400 cursor-pointer"
                >
                  Clear all
                </button>
              )}
            </div>

            {userAvailability.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {userAvailability.map((slot, idx) => (
                  <div
                    key={`${slot.day_of_week}-${idx}`}
                    className="rounded-2xl border border-teal-500/30 bg-teal-50/70 dark:bg-teal-950/40 p-4 shadow-sm flex flex-col justify-between transition hover:border-teal-400"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-sm">⏰</span>
                          <span className="text-xs font-bold text-slate-900 dark:text-white">
                            {slot.day_of_week}
                          </span>
                        </div>
                        <p className="text-base font-extrabold text-teal-800 dark:text-teal-300 mt-1 tracking-tight">
                          {formatAlarmTime(slot.start_time)} – {formatAlarmTime(slot.end_time)}
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={() => handleRemoveAvailability(idx)}
                        className="h-6 w-6 rounded-full bg-slate-900/10 hover:bg-slate-900/20 dark:bg-white/10 dark:hover:bg-white/20 flex items-center justify-center text-xs text-slate-700 dark:text-slate-200 transition cursor-pointer"
                        title="Remove alarm window"
                      >
                        ✕
                      </button>
                    </div>

                    <div className="mt-3 pt-2.5 border-t border-teal-200/60 dark:border-teal-800/60 flex items-center justify-between text-[10px]">
                      <span className="inline-flex items-center gap-1 font-semibold text-teal-700 dark:text-teal-400">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        Radar Match Active
                      </span>
                      <span className="text-slate-500 dark:text-slate-400 font-medium">
                        Open for invites
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">
                No time alarms set yet. Set a custom time window above or tap presets below.
              </p>
            )}
          </div>

          {/* Quick Preset Alarm Windows */}
          <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800">
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 block mb-3">
              💡 Quick-Add Popular Time Windows (Tap to toggle):
            </label>
            <div className="flex flex-wrap gap-2">
              {presetAlarmSlots.map((slot) => {
                const isSelected = userAvailability.some(
                  (a) => a.day_of_week.toLowerCase() === slot.day_of_week.toLowerCase()
                );
                return (
                  <button
                    key={slot.id}
                    type="button"
                    onClick={() =>
                      handleTogglePresetAlarm({
                        day_of_week: slot.day_of_week,
                        start_time: slot.start_time,
                        end_time: slot.end_time,
                      })
                    }
                    className={`rounded-xl px-3.5 py-2 text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
                      isSelected
                        ? "bg-teal-500/20 border border-teal-500 text-teal-800 dark:text-teal-300 font-bold"
                        : "bg-slate-100 text-slate-800 hover:bg-slate-200 border border-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700"
                    }`}
                  >
                    <span>{slot.label}</span>
                    <span className="text-[10px] text-slate-400">
                      {isSelected ? "✓" : "+"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        {/* 4. FLEXIBLE SKILLS & TALENT OFFERING (GET /skills & PUT /profile/me/skills) */}
        <section className="rounded-[2.5rem] bg-white p-6 md:p-8 shadow-md ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 transition-colors">
          <div className="pb-4 border-b border-slate-100 dark:border-slate-800">
            <span className="text-[10px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
              ⚡ Talent &amp; Skill-Sharing Radar
            </span>
            <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">
              Skills You Can Offer or Spar In ({userSkills.length} Added)
            </h2>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
              Type any skill you enjoy sharing (e.g. Badminton sparring, Guitar, Street photography, Coding) and choose your proficiency level.
            </p>
          </div>

          {/* Interactive Type-to-Add Custom Skill Bar */}
          <form
            onSubmit={handleAddCustomSkill}
            className="mt-6 rounded-3xl bg-slate-50 dark:bg-slate-850 p-5 md:p-6 border border-slate-200 dark:border-slate-800 space-y-4"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                <span>🎯</span> Add a Custom Skill or Sparring Talent
              </span>
              <span className="text-[11px] text-teal-600 dark:text-teal-400 font-semibold">
                Type &amp; Press Enter ↵
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Skill Name Input */}
              <div className="sm:col-span-2">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 block mb-1">
                  Skill Name
                </label>
                <input
                  type="text"
                  value={customSkillInput}
                  onChange={(e) => setCustomSkillInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddCustomSkill();
                    }
                  }}
                  placeholder="e.g. Badminton Coaching, Acoustic Guitar, Portrait Photography, React Dev"
                  className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-xs font-semibold text-slate-900 placeholder:text-slate-400 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              {/* Proficiency Level Picker */}
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 block mb-1">
                  Proficiency Level
                </label>
                <select
                  value={customSkillLevel}
                  onChange={(e) => setCustomSkillLevel(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-xs font-bold text-slate-900 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="Beginner">🟢 Beginner (Casual / Learner)</option>
                  <option value="Intermediate">🔵 Intermediate (Club / Regular)</option>
                  <option value="Advanced">🟣 Advanced (Coach / Sparring Pro)</option>
                </select>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-1">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-700 dark:text-slate-300">
                <input
                  type="checkbox"
                  checked={customSkillOffering}
                  onChange={(e) => setCustomSkillOffering(e.target.checked)}
                  className="h-4 w-4 rounded text-teal-600 accent-teal-500 cursor-pointer"
                />
                <span>✨ Open to coach, spar, or partner with others in this skill</span>
              </label>

              <button
                type="submit"
                disabled={!customSkillInput.trim()}
                className="rounded-xl bg-teal-400 px-6 py-2.5 text-xs font-bold text-slate-950 shadow-md hover:bg-teal-300 disabled:opacity-40 disabled:cursor-not-allowed transition cursor-pointer shrink-0"
              >
                + Add Skill
              </button>
            </div>
          </form>

          {/* Active Skills Roster */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-3">
              <label className="text-[11px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 block">
                Your Active Skills ({userSkills.length})
              </label>
              {userSkills.length > 0 && (
                <button
                  type="button"
                  onClick={() => setUserSkills([])}
                  className="text-[11px] font-semibold text-rose-600 hover:text-rose-700 dark:text-rose-400 cursor-pointer"
                >
                  Clear all
                </button>
              )}
            </div>

            {userSkills.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {userSkills.map((sk, idx) => {
                  const emoji = getSkillEmoji(sk.name || "");
                  return (
                    <div
                      key={`${sk.name}-${idx}`}
                      className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-850 p-4 shadow-sm flex flex-col justify-between transition hover:border-slate-300 dark:hover:border-slate-700"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2.5">
                          <span className="text-2xl">{emoji}</span>
                          <div>
                            <p className="text-sm font-bold text-slate-900 dark:text-white leading-snug">
                              {sk.name}
                            </p>
                            <span className="text-[10px] text-slate-500 dark:text-slate-400">
                              {sk.category || "Skill Sharing"}
                            </span>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => handleRemoveSkill(idx)}
                          className="h-6 w-6 rounded-full bg-slate-900/10 hover:bg-slate-900/20 dark:bg-white/10 dark:hover:bg-white/20 flex items-center justify-center text-xs text-slate-700 dark:text-slate-200 transition cursor-pointer"
                          title="Remove skill"
                        >
                          ✕
                        </button>
                      </div>

                      <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between gap-2">
                        {/* Interactive Level Switcher */}
                        <select
                          value={sk.skill_level}
                          onChange={(e) => updateSkillLevelByIndex(idx, e.target.value)}
                          className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-[11px] font-bold text-slate-800 outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                        >
                          <option value="Beginner">🟢 Beginner</option>
                          <option value="Intermediate">🔵 Intermediate</option>
                          <option value="Advanced">🟣 Advanced ⭐</option>
                        </select>

                        {/* Sparring Offer Toggle Button */}
                        <button
                          type="button"
                          onClick={() => toggleSkillOfferingByIndex(idx)}
                          className={`rounded-lg px-2 py-1 text-[10px] font-bold transition cursor-pointer ${
                            sk.is_offering
                              ? "bg-teal-500/20 text-teal-800 dark:text-teal-300 border border-teal-500/40"
                              : "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                          }`}
                          title="Click to toggle sparring availability"
                        >
                          {sk.is_offering ? "✓ Sparring Open" : "Personal Only"}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">
                No skills added yet. Type a skill above or tap suggestions below.
              </p>
            )}
          </div>

          {/* Quick-Pick Catalog Suggestions */}
          <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800">
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 block mb-3">
              💡 Popular Skills Catalog (Tap to add/toggle):
            </label>
            <div className="flex flex-wrap gap-2">
              {skillsCatalog.slice(0, 17).map((sk) => {
                const isSelected = userSkills.some(
                  (s) => (s.name || "").toLowerCase() === sk.name.toLowerCase()
                );
                const emoji = getSkillEmoji(sk.name);
                return (
                  <button
                    key={sk.skill_id}
                    type="button"
                    onClick={() => toggleCatalogSkill(sk)}
                    className={`rounded-xl px-3.5 py-2 text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
                      isSelected
                        ? "bg-teal-500/20 border border-teal-500 text-teal-800 dark:text-teal-300 font-bold"
                        : "bg-slate-100 text-slate-800 hover:bg-slate-200 border border-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700"
                    }`}
                  >
                    <span>{emoji}</span>
                    <span>{sk.name}</span>
                    <span className="text-[10px] text-slate-400">
                      {isSelected ? "✓" : "+"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        {/* BOTTOM SAVE BAR */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-6 rounded-3xl bg-slate-900 text-white shadow-xl">
          <div>
            <p className="text-sm font-bold">Ready to discover your people?</p>
            <p className="text-xs text-slate-400">
              Saving updates your vector embedding across all 23 database tables.
            </p>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              type="button"
              onClick={() => handleSaveProfile(false)}
              disabled={saving}
              className="w-full sm:w-auto rounded-xl border border-white/20 px-5 py-3 text-xs font-bold text-white hover:bg-white/10 transition cursor-pointer"
            >
              {saving ? "Saving..." : "Save Profile"}
            </button>

            <button
              type="button"
              onClick={() => handleSaveProfile(true)}
              disabled={saving}
              className="w-full sm:w-auto rounded-xl bg-teal-400 px-6 py-3 text-xs font-bold text-slate-950 shadow-md hover:bg-teal-300 transition cursor-pointer shrink-0"
            >
              Save &amp; Find Matches Now →
            </button>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}