/** Phone photos arrive at 12 MP and several MB. Measuring needs far less:
 * registration lines the recipe up at any scale, and a deposit is still
 * tens of pixels across at 1600 px. Shrinking in the browser keeps the
 * upload quick on booth Wi-Fi and the stored annotated image small. */
const MAX_SIDE = 1600;

export async function preparePhoto(file: File): Promise<File> {
  if (typeof createImageBitmap === "undefined" || !file.type.startsWith("image/")) return file;
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
    const longest = Math.max(bitmap.width, bitmap.height);
    if (longest <= MAX_SIDE) {
      bitmap.close();
      return file;
    }
    const scale = MAX_SIDE / longest;
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    canvas.getContext("2d")?.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close();
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
    if (!blob) return file;
    return new File([blob], file.name.replace(/\.\w+$/, "") + ".jpg", { type: "image/jpeg" });
  } catch {
    return file; // an image the browser can't decode is the backend's to refuse, with its reason
  }
}
