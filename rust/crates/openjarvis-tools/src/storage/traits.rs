//! MemoryBackend trait for all storage backends.

use ethan_core::{EthanError, RetrievalResult};
use serde_json::Value;

pub trait MemoryBackend: Send + Sync {
    fn backend_id(&self) -> &str;
    fn store(
        &self,
        content: &str,
        source: &str,
        metadata: Option<&Value>,
    ) -> Result<String, EthanError>;
    fn retrieve(
        &self,
        query: &str,
        top_k: usize,
    ) -> Result<Vec<RetrievalResult>, EthanError>;
    fn delete(&self, doc_id: &str) -> Result<bool, EthanError>;
    fn clear(&self) -> Result<(), EthanError>;
    fn count(&self) -> Result<usize, EthanError>;
}
