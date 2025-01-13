function getFirebaseAuthToken() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("firebaseLocalStorageDb");

    request.onerror = (event) => {
      reject(
        JSON.stringify({
          error: "IndexedDB açılırken hata",
          details: event.target.error,
        })
      );
    };

    request.onsuccess = (event) => {
      const db = event.target.result;
      const transaction = db.transaction(["firebaseLocalStorage"], "readonly");
      const objectStore = transaction.objectStore("firebaseLocalStorage");

      const getAllRequest = objectStore.getAll();

      getAllRequest.onsuccess = (event) => {
        const items = event.target.result;
        const authData = items.find((item) => item.fbase_key.startsWith("firebase:authUser:"));

        if (authData?.value) {
          const tokenData = {
            apiKey: authData.value.apiKey,
            accessToken: authData.value.stsTokenManager.accessToken,
            refreshToken: authData.value.stsTokenManager.refreshToken,
            expirationTime: authData.value.stsTokenManager.expirationTime,
          };
          resolve(JSON.stringify(tokenData, null, 2));
        } else {
          reject(
            JSON.stringify({
              error: "Auth verisi bulunamadı",
            })
          );
        }
      };

      getAllRequest.onerror = (event) => {
        reject(
          JSON.stringify({
            error: "Veri alınırken hata",
            details: event.target.error,
          })
        );
      };
    };
  });
}
