import { authAxios } from '$auth/state/auth';

export const deletePrototype = async (prototypeId: string) => {
  return await authAxios.delete(`/v1/generator/prototypes/${prototypeId}`);
};