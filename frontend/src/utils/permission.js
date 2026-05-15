export function hasPermission(user, code) {
  return Boolean(user?.permissions?.includes(code));
}
