"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();
    const { toast } = useToast();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!email || !password) {
            toast({
                title: "Please fill in all fields",
                variant: "destructive",
            });
            return;
        }

        setLoading(true);

        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_BASE}/auth/login`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ email: email.trim(), password }),
                },
            );

            if (!response.ok) {
                const errorText = await response.text().catch(() => "");
                const isUnauthorized = response.status === 401;
                const baseMessage = isUnauthorized
                    ? "Invalid email or password"
                    : "Unable to sign in.";

                const description =
                    errorText ||
                    (isUnauthorized
                        ? "Please check your credentials and try again."
                        : `Make sure the backend is reachable at ${process.env.NEXT_PUBLIC_API_BASE}.`);

                toast({
                    title: baseMessage,
                    description,
                    variant: "destructive",
                });
                return;
            }

            const data = await response.json();

            if (typeof window !== "undefined") {
                try {
                    window.localStorage.setItem("authToken", data.access_token);
                    window.localStorage.setItem(
                        "authUser",
                        JSON.stringify(data.user),
                    );
                } catch {
                    // Ignore storage errors; login can still proceed.
                }
            }

            toast({ title: "Signed in successfully" });
            router.push("/dashboard");
        } catch (err: any) {
            const msg = err?.message || "";
            const isNet =
                msg === "Failed to fetch" ||
                msg.includes("NetworkError") ||
                msg.includes("Load failed");

            const userMsg = isNet
                ? `Cannot reach API at ${process.env.NEXT_PUBLIC_API_BASE}. Make sure the backend is running.`
                : msg || "Login failed.";

            toast({
                title: "Sign-in failed",
                description: userMsg,
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top,_hsl(230_94%_68%_/_0.18),_transparent_55%),radial-gradient(circle_at_bottom,_hsl(270_88%_68%_/_0.14),_transparent_55%)]">
            {/* Soft grid / glow background */}
            <div className="pointer-events-none absolute inset-0 opacity-40 [background-image:radial-gradient(circle_at_1px_1px,hsl(var(--border)_/_0.35)_1px,transparent_0)] [background-size:32px_32px]" />

            <div className="relative z-10 flex min-h-screen items-center justify-center px-4">
                <div className="relative w-full max-w-md">
                    {/* Glass login card */}
                    <div className="glass-card relative overflow-hidden rounded-3xl border border-border/60 bg-card/80 p-8 shadow-xl">
                        <div className="pointer-events-none absolute inset-x-10 -top-16 h-32 rounded-full bg-gradient-to-r from-primary/25 via-accent/25 to-primary/10 blur-3xl" />

                        <div className="relative space-y-6">
                            <div className="space-y-2 text-center">
                                <h1 className="text-3xl font-semibold tracking-tight">
                                    Welcome back
                                </h1>
                                <p className="text-sm text-muted-foreground">
                                    Sign in to continue crafting AI-powered
                                    estimates and proposals.
                                </p>
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="email">Email</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        placeholder="you@company.com"
                                        value={email}
                                        onChange={(e) =>
                                            setEmail(e.target.value)
                                        }
                                        className="h-11"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="password">Password</Label>
                                    <Input
                                        id="password"
                                        type="password"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) =>
                                            setPassword(e.target.value)
                                        }
                                        className="h-11"
                                    />
                                </div>
                                <Button
                                    type="submit"
                                    className="w-full h-11 btn-primary-glow"
                                    disabled={loading}
                                >
                                    {loading ? "Signing in..." : "Sign In"}
                                </Button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
