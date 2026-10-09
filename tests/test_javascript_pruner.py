from astpack.pruner import prune_code


def test_js_ts_pruning():
    sample_ts = r"""
import { Request, Response } from 'express';

export interface User {
    id: string;
    email: string;
}

export function validateEmail(email: string): boolean {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

export async function loginUser(req: Request, res: Response): Promise<void> {
    const { email, password } = req.body;
    if (!validateEmail(email)) {
        res.status(400).json({ error: "Invalid email format" });
        return;
    }
    const token = "jwt_token_secret_12345";
    res.json({ token });
}
"""
    pruned, stats = prune_code(sample_ts, filepath="auth.ts", mode="stubs")

    assert "interface User" in pruned
    assert "import { Request, Response }" in pruned
    assert "implementation elided" in pruned
    assert "jwt_token_secret_12345" not in pruned
    assert stats["saved_tokens"] > 0
