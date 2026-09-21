import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";

// AES-GCM standard sizes: 96-bit (12-byte) nonce is the recommended size
// for GCM, and the authentication tag is fixed at 128 bits (16 bytes).
const NONCE_SIZE = 12;
const TAG_SIZE = 16;

/**
 * Reads and validates the AES-256 key from LOCKER_ENCRYPTION_KEY. This key
 * never leaves the client — it's not sent to the API, not stored anywhere
 * but the caller's own environment — so failing loudly on a missing/wrong
 * key here is safer than silently proceeding with the wrong one.
 */
function loadKey(): Buffer {
  const encoded = process.env.LOCKER_ENCRYPTION_KEY;
  if (!encoded) {
    throw new Error(
      "LOCKER_ENCRYPTION_KEY is not set. Generate one with:\n" +
        '  node -e "console.log(require(\'crypto\').randomBytes(32).toString(\'base64\'))"\n' +
        "and keep it off the server. This is a placeholder for the DEK/KEK + " +
        "recovery-phrase flow described in BACKLOG.md — a single static key is " +
        "enough to prove the server never sees plaintext, not the finished " +
        "key-management story.",
    );
  }
  const key = Buffer.from(encoded, "base64");
  if (key.length !== 32) {
    throw new Error("LOCKER_ENCRYPTION_KEY must decode to 32 bytes (AES-256).");
  }
  return key;
}

/**
 * Encrypts `plaintext` with AES-256-GCM using a fresh random nonce per call
 * (never reused — reusing a nonce with the same key breaks GCM's security
 * guarantees entirely).
 *
 * Wire format: base64(nonce ‖ ciphertext ‖ tag). This matches crypto.py's
 * Python implementation byte for byte, so content encrypted by one client
 * (Node or Python) is always decryptable by the other — verified directly,
 * not just assumed, in this project's test suite.
 */
export function encrypt(plaintext: string): string {
  const key = loadKey();
  const nonce = randomBytes(NONCE_SIZE);
  const cipher = createCipheriv("aes-256-gcm", key, nonce);
  const ciphertext = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([nonce, ciphertext, tag]).toString("base64");
}

/**
 * Reverses `encrypt`. Throws if the key is wrong or the ciphertext/tag has
 * been tampered with — GCM's authentication tag makes silent corruption
 * impossible; decryption either returns the exact original plaintext or
 * throws, never a garbled result.
 */
export function decrypt(encoded: string): string {
  const key = loadKey();
  const raw = Buffer.from(encoded, "base64");
  const nonce = raw.subarray(0, NONCE_SIZE);
  const tag = raw.subarray(raw.length - TAG_SIZE);
  const ciphertext = raw.subarray(NONCE_SIZE, raw.length - TAG_SIZE);
  const decipher = createDecipheriv("aes-256-gcm", key, nonce);
  decipher.setAuthTag(tag);
  const plaintext = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
  return plaintext.toString("utf8");
}
