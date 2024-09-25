import { authAxios } from '$auth/state/auth';

export const deleteInterface = async (interfaceId: string) => {
  return await authAxios.delete(`/v1/metadata/interfaces/${interfaceId}`);
};