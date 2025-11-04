export const addFiles = async (
  files,
  user_id = "test_user",
  room_id = "1",
  session_id = "user_1755047917647_1758266384487"
) => {
  const res = await fetch("ui.datastreams.co.kr:20443/v1/addFile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      files: files,
      user_id: user_id,
      room_id: room_id,
      session_id: session_id,
    }),
  });

  if (!res.ok) throw new Error("Failed to fetch settings");
  return await res.json();
};

export const deleteFiles = async (
  files,
  user_id = "test_user",
  room_id = "1",
  session_id = "user_1755047917647_1758266384487"
) => {
  const res = await fetch("ui.datastreams.co.kr:20443/v1/detailHistory", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      files: files,
      user_id: user_id,
      room_id: room_id,
      session_id: session_id,
    }),
  });

  if (!res.ok) throw new Error("Failed to fetch settings");
  return await res.json();
};

export const deleteAllFiles = async (
  user_id = "test_user",
  room_id = "1",
  session_id = "user_1755047917647_1758266384487"
) => {
  const res = await fetch("ui.datastreams.co.kr:20443/v1/detailHistory", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: user_id,
      room_id: room_id,
      session_id: session_id,
    }),
  });

  if (!res.ok) throw new Error("Failed to fetch settings");
  return await res.json();
};
